# SabiPass AI Library Audit

Date: 2026-05-19

Scope: research and audit only. No implementation code was changed, and the
implementation plan was not updated.

Session entry context read:

- `CODEX_MASTER_DIRECTIVE.md`
- `docs/ARCHITECTURE.md`
- `docs/ENGINEERING_GUIDELINES.md`

## Executive Summary

The codebase is currently in an MVP-friendly state: many important components
are either intentionally deterministic, hand-rolled, or stubbed. That is useful
for proving the layer boundaries, but the production path should replace the
highest-risk manual pieces with maintained libraries.

The strongest immediate library fits are:

- `pyBKT` for Bayesian Knowledge Tracing instead of the fixed BKT placeholder.
- `sentence-transformers` or `FastEmbed` instead of deterministic hash
  embeddings and token-overlap semantic matching.
- `SymPy`, `latex2sympy2-extended`, and `Math-Verify` for math parsing,
  solving, and equivalence checking instead of new custom math logic.
- `cachetools` and `diskcache` for bounded MVP caching without Redis.
- `structlog` and OpenTelemetry Python for observability instead of bespoke
  JSONL-only tracing.
- `Hypothesis`, `Factory Boy`, `Faker`, and `pytest-benchmark` for broader
  tests and generated request data.

The strongest caution is that several excellent AI libraries would conflict
with SabiPass's current architecture if adopted wholesale. Haystack, LangChain,
LlamaIndex, Rasa, Guardrails, and pyKT can all be valuable, but only if used
behind existing SabiPass boundaries. They should not take over strategy
compilation, request orchestration, provider selection, Node-owned student
state, or the LiteLLM-only LLM path.

## Current Manual Or Basic Surfaces Found

- `app/services/bkt_engine.py` returns fixed mastery metrics.
- `app/rag/embeddings.py` uses deterministic 16-dimensional hash embeddings.
- `app/services/strategy/concept_normalizer.py` uses regex, alias matching,
  and token-overlap scoring for "semantic" matching.
- `app/services/strategy/intent_parser.py` uses keyword lists for intents.
- `app/services/strategy/complexity_scorer.py` uses hand-weighted rules.
- `app/math/*.py` and `app/services/math_verifier.py` are stubs.
- `app/rag/retriever.py` manually parses Chroma results and confidence.
- `app/services/rag_router.py` manually handles RAG mode selection,
  fallback-summary JSON loading, and `functools.lru_cache`.
- `app/core/config.py` manually parses environment variables.
- `app/observability/*.py` and `app/schemas/traces.py` are observability stubs.
- `app/governance/*.py` and `app/schemas/governance.py` are governance stubs.
- `app/registry/snapshot.py` manually loads and freezes registry JSON.
- `pipelines/ingestion/*.py` manually parse mock JSON, validate metadata, and
  seed Chroma.
- Several test modules duplicate payload builders and use fixed examples.
- `tests/evaluation/test_retrieval_quality.py` is empty.

## Architecture Constraints That Affect Library Choices

- Python owns cognition only. Node.js owns auth, payment, persisted student
  state, idempotency, Teach First gating, and Supabase state.
- MVP explicitly excludes Redis and Kubernetes.
- All LLM calls must go through LiteLLM. No direct provider SDK calls should
  appear outside the approved execution path.
- `app/services/rag_router.py` remains the service-level RAG entry point, and
  `app/rag/retriever.py` remains the low-level retrieval utility.
- Request handlers must avoid disk I/O except Chroma reads.
- Layer 2 `StateStrategy` must remain immutable and must not be reinterpreted
  downstream.
- Chroma is the current architecture decision for MVP vector storage.

## Recommendation Matrix

### BKT And Student Knowledge Modelling

| Library | What it replaces | Why it is better for production | Replacement type | Architecture conflicts |
| --- | --- | --- | --- | --- |
| [`pyBKT`](https://github.com/CAHLR/pyBKT) | `app/services/bkt_engine.py`, which currently returns fixed `updated_bkt_mastery`, `calculated_learning_velocity`, and `updated_weakness_array`. | It is purpose-built for Bayesian Knowledge Tracing and estimates mastery from problem-solving sequences instead of using static values. It is directly aligned with the codebase's BKT requirement and is already listed in `requirements.txt`. | Refactor, not drop-in. The API layer must transform Node-supplied attempts/history into pyBKT's expected interaction data and return only stateless deltas to Node. | No major conflict if Python remains stateless. Do not let Python persist per-student mastery; Node/Supabase remains the source of truth. |
| [`pyKT`](https://github.com/pykt-team/pykt-toolkit) | Future hand-rolled deep knowledge tracing or ad hoc learning-velocity models in `app/services/learning_state_adapter.py` and `app/models/cognitive/`. | It benchmarks many deep knowledge tracing approaches on standardized datasets, which is much stronger than inventing a neural KT model. | Major refactor and offline-research adoption only. | It conflicts with MVP latency and simplicity if used in the request path. Use only for offline model exploration after enough SabiPass interaction data exists. |
| [`River`](https://github.com/online-ml/river) | Manual learning velocity, decay, and online behavior scoring that would otherwise be built around counters and slopes. | It is designed for streaming and continual learning, which matches per-attempt student signals better than batch-only ML. | Refactor. It can power small online estimators behind a stateless adapter. | Must not persist student state inside Python. River state would need to be serialized by Node or used only for aggregate/offline analysis. |

### Embeddings And Semantic Similarity

| Library | What it replaces | Why it is better for production | Replacement type | Architecture conflicts |
| --- | --- | --- | --- | --- |
| [`sentence-transformers`](https://www.sbert.net/) | `app/rag/embeddings.py` deterministic hash embeddings and token-overlap matching in `concept_normalizer.py`. | It provides trained dense embeddings, semantic similarity, semantic search, reranking, sparse encoders, and fine-tuning paths. This is a production AI default for local semantic retrieval. | Refactor. The existing `EmbeddingFunction = Callable[[str], Sequence[float]]` seam makes this straightforward, but vector dimensions and existing Chroma data must be reindexed. | Model loading must happen outside hot request paths. Pick a small multilingual or cross-lingual model for English/Pidgin-like input and benchmark latency. |
| [`FastEmbed`](https://qdrant.github.io/fastembed/) | Hash embeddings in API and ingestion paths, especially `seed_mock_exam_bank(..., embed_text=deterministic_text_embedding)`. | It uses ONNX Runtime, supports dense/sparse/reranking models, and is designed for lightweight local embedding generation. | Mostly drop-in behind the current embedding callable, but requires dimension changes and reindexing. | No architectural conflict. It is a good MVP-compatible option because it avoids remote embedding calls. |
| [`FlagEmbedding`](https://github.com/FlagOpen/FlagEmbedding) | Future custom multilingual embedding/reranking logic for WAEC/JAMB content. | It includes strong BGE models such as BGE-M3 for dense, sparse, and multi-vector retrieval. | Refactor. Better as an offline/indexing or premium retrieval experiment than the first MVP embedding runtime. | Larger model footprint may violate latency and memory budgets on a single small Render/Railway service. |
| [`spaCy`](https://spacy.io/usage/processing-pipelines) | Regex-only normalization, Pidgin signal detection, and token cleanup in `concept_normalizer.py`, `intent_parser.py`, and `tutor_engine.py`. | It provides production NLP pipelines, tokenization, text categorization, batching, and custom components. | Refactor. Keep current registry alias logic as deterministic first pass; use spaCy for language processing and classifiers. | Requires model packaging and startup loading. Avoid putting a large transformer pipeline into the request path without benchmarks. |

### Math Parsing, Solving, And Equivalence Checking

| Library | What it replaces | Why it is better for production | Replacement type | Architecture conflicts |
| --- | --- | --- | --- | --- |
| [`SymPy`](https://docs.sympy.org/latest/index.html) | Empty stubs in `app/math/normalizer.py`, `app/math/equivalence.py`, `app/math/sympy_worker.py`, and `app/services/math_verifier.py`. | It is the standard open-source Python symbolic mathematics library, with equation solving, simplification, parsing, and symbolic equality tools. | Refactor, but architecturally expected. | Must run in the bounded process pool described in `docs/ARCHITECTURE.md`; do not run heavy symbolic work directly in FastAPI handlers. |
| [`latex2sympy2-extended`](https://github.com/huggingface/latex2sympy2_extended) | Any future regex parser for LaTeX-like student math input. | It converts LaTeX math into SymPy expressions and builds on the same symbolic stack. | Refactor. Use only inside the math normalization layer. | Parser failures must become micro-clarifications, not confident answers. Pin ANTLR/runtime versions to avoid parser drift. |
| [`Math-Verify`](https://github.com/huggingface/Math-Verify) | Custom final-answer equivalence checks, especially for LLM-produced math answers and worked solutions. | It is designed to parse and verify mathematical answers from LLM outputs, with numerical and symbolic comparison support. | Refactor. It should sit behind `app/services/math_verifier.py` and feed the existing response/audit path. | It should complement, not replace, direct SymPy checks. Treat it as an evaluator/verifier, not as the tutor decision engine. |

### Vector Retrieval And RAG

| Library | What it replaces | Why it is better for production | Replacement type | Architecture conflicts |
| --- | --- | --- | --- | --- |
| [`Chroma`](https://docs.trychroma.com/docs/overview/introduction) with real embeddings | The current manual Chroma wrapper is acceptable, but it is fed by fake deterministic vectors. | Chroma already supports vector storage, metadata filtering, and local/self-hosted use, matching the MVP architecture. The production gain comes from real embeddings, better indexing discipline, and retrieval evaluation. | Keep, then refactor ingestion/indexing around real embedding functions. | No conflict. Chroma is the current architecture decision. |
| [`Qdrant Client`](https://python-client.qdrant.tech/) | A future replacement for `app/db/chroma.py` if Chroma persistence/concurrency becomes limiting. | Qdrant is a dedicated vector search engine with Python sync/async clients, payload filters, and production deployment options. | Not drop-in. Requires DB adapter work, deployment changes, and data migration. | Conflicts with current Chroma architecture and "no new infra" MVP constraint. Treat as post-MVP infrastructure evaluation. |
| [`Haystack`](https://docs.haystack.deepset.ai/docs/intro) | Future hand-rolled RAG evaluation/indexing pipelines, chunk cleaning, retrievers, rankers, and document-store integrations. | It is a production-oriented open-source framework for RAG pipelines with explicit components. | Partial refactor. Use components selectively for ingestion/evaluation or behind `app/rag/`; do not replace `StateStrategy` or `rag_router` wholesale. | Full-pipeline adoption would conflict with SabiPass's layer ownership. Keep SabiPass routing and pedagogy decisions outside Haystack. |
| [`LlamaIndex`](https://docs.llamaindex.ai/) | Future custom document ingestion, node parsing, indexing, and retrieval helpers. | It is widely used for data-to-LLM indexing and retrieval workflows. | Refactor and limited adoption. Best suited for offline ingestion experiments. | If used to orchestrate query-time RAG, it conflicts with `rag_router` and immutable `StateStrategy`. |
| [`Ragas`](https://docs.ragas.io/en/stable/tutorials/rag/) or [`DeepEval`](https://deepeval.com/docs/introduction) | Empty retrieval evaluation test and future bespoke RAG quality scoring. | Both provide ready-made RAG/LLM evaluation patterns; DeepEval is pytest-native, while Ragas focuses on RAG metrics. | Additive, not drop-in. Use in evaluation tests and CI, not request code. | LLM-as-judge metrics may violate deterministic eval requirements unless configured with cached/local judge outputs. |

### Intent Classification And NLP

| Library | What it replaces | Why it is better for production | Replacement type | Architecture conflicts |
| --- | --- | --- | --- | --- |
| [`SetFit`](https://huggingface.co/docs/setfit/index) | Keyword-only `parse_intent()` in `app/services/strategy/intent_parser.py`. | It is a prompt-free few-shot text classification framework built on Sentence Transformers, useful when labeled SabiPass intent examples are still small. | Refactor. Start with labels from current tests and session data; keep keyword overrides for high-precision emergency cases. | Requires a training/evaluation loop and model artifact management. Do not call remote models in Layer 2. |
| [`scikit-learn`](https://scikit-learn.org/stable/modules/feature_extraction.html) | Manual intent weights and future lightweight classifiers. | TF-IDF plus linear classifiers are fast, explainable, small, and easy to run locally for MVP intent routing. | Refactor. Good first ML replacement before neural classifiers. | Needs labeled data. Does not solve Pidgin semantics by itself without local examples. |
| [`Rasa Open Source`](https://rasa.com/docs/reference/primitives/intents-and-entities/) | Any future attempt to build a full NLU/dialogue manager inside this microservice. | Rasa has mature intent/entity primitives and regex/lookup support. | Not recommended as an immediate replacement. Use only if SabiPass creates a separate conversational NLU service. | Conflicts with Python being a cognition microservice, not the chat backend or dialogue manager. |

### API Performance And Request Handling

| Library | What it replaces | Why it is better for production | Replacement type | Architecture conflicts |
| --- | --- | --- | --- | --- |
| [`orjson`](https://github.com/ijl/orjson) | Standard `json` usage in registry, fallback summaries, ingestion files, and possibly FastAPI response serialization. | It is a fast, strict JSON library with native dataclass, datetime, UUID, and NumPy support. | Mostly drop-in for JSON serialization/deserialization and FastAPI `ORJSONResponse`. | No major conflict. Be careful that it returns bytes and is stricter than stdlib `json`. |
| [`uvicorn[standard]` / `uvloop`](https://github.com/MagicStack/uvloop) | Default asyncio event loop and plain Uvicorn runtime choices. | `uvloop` is a high-performance drop-in asyncio event loop; Uvicorn can use it in production Linux deployments. | Drop-in deployment/config dependency, not code-level replacement. | No conflict. Windows local dev may fall back to default asyncio. |
| [`pydantic-settings`](https://pydantic.dev/docs/validation/2.12/concepts/pydantic_settings/) | Manual environment parsing in `app/core/config.py`. | It gives typed, validated, documented config from env vars and `.env` files. | Refactor. Centralize all tier/model/history/cache/worker settings in one settings object. | No conflict. Preserve existing env var names for Node/deploy compatibility. |
| [`SlowAPI`](https://slowapi.readthedocs.io/) or [`limits`](https://slowapi.readthedocs.io/en/stable/api/) | Any future bespoke rate limiter or emergency overload guard. | It provides Starlette/FastAPI-compatible rate limiting using the `limits` ecosystem. | Additive, not drop-in. | Node owns product rate limits and idempotency. Redis-backed limits conflict with MVP; in-memory fallback only protects a single process. |
| [`HTTPX`](https://www.python-httpx.org/) | `requests` in `streamlit_test/app.py` and any future internal HTTP calls. | It supports sync and async APIs, HTTP/2, timeouts, and a requests-like API. | Optional refactor. Streamlit can remain on `requests`; API internals should prefer HTTPX if new HTTP clients are needed. | No conflict, but Python should not add Supabase/product-backend fetches that violate architecture. |

### Caching

| Library | What it replaces | Why it is better for production | Replacement type | Architecture conflicts |
| --- | --- | --- | --- | --- |
| [`cachetools`](https://cachetools.readthedocs.io/) | `functools.lru_cache` in `rag_router.py`, `_CLIENTS_BY_PATH` in `app/db/chroma.py`, and any future in-memory TTL caches. | It provides explicit `TTLCache`, `LRUCache`, and size-limited caches instead of unversioned function-level caching. | Mostly drop-in for small in-memory caches. | No conflict. It remains per-process, which is acceptable for MVP but not cross-worker consistency. |
| [`diskcache`](https://pypi.org/project/diskcache/) | Future hand-built file-backed review queue, LLM mock cache, evaluation cache, and fallback-summary cache. | It is a persistent disk-backed cache built on SQLite and usable without a separate Redis process. | Refactor. Good for MVP background/evaluation caches. | Request handlers must not block on disk writes. Use only in background workers or offline scripts. |
| [`redis-py`](https://redis.io/docs/latest/develop/clients/redis-py/) | Future multi-worker idempotency, cache stampede control, distributed review queues, and shared rate limits. | Redis is the common production cache/queue primitive. | Future infrastructure refactor only. | Explicitly conflicts with "No Redis for MVP." Defer until production scale requires cross-process shared state. |

### Structured Logging And Observability

| Library | What it replaces | Why it is better for production | Replacement type | Architecture conflicts |
| --- | --- | --- | --- | --- |
| [`structlog`](https://www.structlog.org/en/stable/index.html) | Future ad hoc `logging` calls and custom JSON log formatting. | It is production-ready structured logging for Python with JSON/logfmt output and context binding. | Refactor. Add as the logging layer for request IDs, registry versions, strategy status, and fallback causes. | No conflict. It should not replace `SystemTrace`; logs and traces serve different jobs. |
| [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/) plus [FastAPI instrumentation](https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/fastapi/fastapi.html) | Stubs in `app/observability/*.py` and future manual tracing. | It is the standard open observability API/SDK for traces and metrics, with FastAPI instrumentation. | Refactor. Use it for request spans, LLM spans, retrieval spans, and error attributes. | Exporters must be non-blocking/batched. Avoid synchronous network exporters on the request path. |
| [`Evidently`](https://docs.evidentlyai.com/docs/library/overview) | Future bespoke drift/quality monitoring for retrieval, intent, and model outputs. | It evaluates and monitors ML/LLM systems and data drift with report/test abstractions. | Additive offline/background tool. | Not request-path. Needs stored traces/eval datasets and should not collect raw student data unless privacy-reviewed. |

### LLM Execution, Structured Output, And Guardrails

| Library | What it replaces | Why it is better for production | Replacement type | Architecture conflicts |
| --- | --- | --- | --- | --- |
| [`LiteLLM Router`](https://docs.litellm.ai/) | Manual fallback/retry/budget logic that would otherwise grow inside `model_router.py` and `llm_executor.py`. | LiteLLM already matches the provider-agnostic architecture and includes routing, retry/fallback, and spend-tracking concepts. | Refactor within the existing LiteLLM-only boundary. | No conflict if all calls remain centralized in `llm_executor.py`. Do not import provider SDKs directly. |
| [`Instructor`](https://python.useinstructor.com/integrations/litellm/) | Future hand-written JSON parsing, schema retry loops, and prompt-based structured output enforcement. | It provides Pydantic-validated structured outputs and has a LiteLLM integration. | Refactor. Good for two-pass plan objects or structured response fragments. | Must be used only through the central LLM executor. Validate provider support and do not let Instructor bypass LiteLLM routing. |
| [`Guardrails AI`](https://guardrailsai.com/guardrails/docs/concepts/guard) | Future custom LLM output validators and repair loops. | It wraps LLM calls and validates outputs against configured guards and Pydantic objects. | Refactor, but use cautiously. | It can conflict with the LiteLLM-only path if it calls providers directly. Prefer using it as validation around existing executor outputs unless integration is clean. |
| [`Tenacity`](https://tenacity.readthedocs.io/en/stable/) | Future hand-written retry loops around transient external calls. | It gives composable retry policies, backoff, and stop conditions. | Mostly drop-in for scripts/offline jobs and non-LLM clients. | For LLM calls, prefer LiteLLM Router first to keep provider behavior centralized. |
| [`aiobreaker`](https://aiobreaker.netlify.app/index.html) | Future hand-built circuit breakers for external model/retrieval services. | It implements the circuit breaker pattern for async Python. | Additive refactor. | Only useful once there are actual external services to protect; keep MVP simple. |

### Ingestion, OCR, And Document Processing

| Library | What it replaces | Why it is better for production | Replacement type | Architecture conflicts |
| --- | --- | --- | --- | --- |
| [`Docling`](https://www.docling.ai/) | Empty `pipelines/ingestion/pdf_parser.py` and future custom PDF/OCR/table/formula parser. | It converts messy documents into structured data and handles layout, OCR, tables, formulas, and reading order. | Major refactor for offline ingestion. | No request-path use. Resource needs must be tested on local/dev machines before CI or Render workers. |
| [`PyMuPDF`](https://pymupdf.readthedocs.io/) and [`PyMuPDF4LLM`](https://github.com/pymupdf/pymupdf4llm) | Basic PDF text extraction and future RAG-oriented markdown/JSON conversion. | PyMuPDF is high-performance PDF extraction/manipulation; PyMuPDF4LLM produces RAG-friendly Markdown/JSON and page chunks. | Refactor. Good first parser for text-extractable PDFs; pair with Docling/OCR for scanned PDFs. | No conflict if kept in offline ingestion. Must preserve the existing loader boundary so replacing the parser changes one file. |
| [`Pydantic`](https://docs.pydantic.dev/) models for ingestion records | Manual metadata validation in `pipelines/ingestion/metadata_validator.py` and typed dataclasses in `documents.py`. | The project already uses Pydantic for API schemas; using it for ingestion would provide consistent validation errors and JSON schema export. | Refactor. | No conflict. Keep strict canonical-topic validation against the concept registry. |
| [`msgspec`](https://github.com/jcrist/msgspec) | High-volume JSON parsing/validation if ingestion grows beyond Pydantic's performance comfort zone. | It combines fast JSON serialization with schema validation using Python type annotations. | Optional refactor for batch ingestion, not API boundary. | It would introduce a second schema system beside Pydantic. Use only if profiling proves Pydantic/json are bottlenecks. |

### Registry, Snapshotting, And File Watching

| Library | What it replaces | Why it is better for production | Replacement type | Architecture conflicts |
| --- | --- | --- | --- | --- |
| [`watchfiles`](https://pypi.org/project/watchfiles/) | Future custom polling in `app/registry/poller.py` for local registry updates. | It is a modern file watcher for Python backed by native filesystem notifications. | Refactor for local/dev and single-server deployments. | Production multi-pod registry consistency still requires shared storage/polling; watchfiles only watches local files. |
| `MappingProxyType` plus Pydantic validation | Current frozen registry snapshot in `app/registry/snapshot.py`. | The immutability approach is good; the missing production piece is schema validation before pointer swap. | Keep and extend. | No conflict. Do not replace with mutable global registries. |

### Testing And Test Data Generation

| Library | What it replaces | Why it is better for production | Replacement type | Architecture conflicts |
| --- | --- | --- | --- | --- |
| [`Hypothesis`](https://github.com/HypothesisWorks/hypothesis) | Hand-picked edge cases for schemas, concept aliases, metadata validation, and math normalization. | Property-based tests can generate many input shapes and shrink failures to minimal examples. It is widely used by major Python projects. | Additive/drop-in for tests. | No conflict. Keep generated tests deterministic in CI by managing seeds/examples. |
| [`Factory Boy`](https://factoryboy.readthedocs.io/) plus [`pytest-factoryboy`](https://pytest-factoryboy.readthedocs.io/en/latest/) | Duplicated request payload builders across tests. | Factories reduce fixture duplication and make scenario-specific overrides cleaner. | Additive test refactor. | No conflict. Keep factories aligned with public Node contract. |
| [`Faker`](https://faker.readthedocs.io/) | Repeated static IDs, timestamps, and synthetic student metadata in tests. | It generates fake data and supports seeding/locales. | Additive test refactor. | Avoid using fake values that violate Nigerian education domain constraints. |
| [`pytest-benchmark`](https://pytest-benchmark.readthedocs.io/) | Informal latency expectations for Layer 2, retrieval, and math. | It integrates benchmark measurements into pytest and helps protect latency budgets. | Additive. | Benchmarks can be noisy in CI. Use thresholds carefully. |
| [`responses`](https://pypi.org/project/responses/) or [`RESPX`](https://lundberg.github.io/respx/guide/) | Manual monkeypatching for `requests`/HTTPX tests. | They mock HTTP calls with request matching and call assertions. | Additive. Use `responses` while Streamlit uses `requests`; use RESPX if moving to HTTPX. | No conflict. External HTTP should remain limited by architecture. |

### Scheduling, Background Work, And Queues

| Library | What it replaces | Why it is better for production | Replacement type | Architecture conflicts |
| --- | --- | --- | --- | --- |
| [`APScheduler`](https://apscheduler.com/) | Future custom interval loops for enrichment, evaluation, trace flushing, and registry checks. | It provides interval/cron/date triggers, job stores, and async/background schedulers. | Refactor for background jobs. | In-process schedulers can duplicate work across multiple workers. Acceptable for MVP single-server only; use external queues later. |
| [`Dramatiq`](https://dramatiq.io/) or Celery/RQ | Future hand-built multi-worker background queues. | Mature task queue libraries are safer than custom multiprocessing/queue logic. | Future infrastructure refactor. | Most production queue backends require Redis/RabbitMQ, which conflicts with MVP constraints. |

## Components That Should Not Be Replaced Wholesale Yet

- FastAPI and Pydantic are already production-grade choices. Improve config and
  serialization around them rather than replacing the API framework.
- LiteLLM is the correct provider abstraction per the master directive. The
  opportunity is to use more of LiteLLM's routing and budget features, not to
  add direct OpenAI/Gemini/Anthropic SDK usage.
- Chroma is acceptable for MVP because the architecture explicitly selected it.
  The bigger current weakness is fake embeddings and limited retrieval
  evaluation, not Chroma itself.
- LangChain, Haystack, and LlamaIndex should not own request orchestration in
  this service. They can be useful for offline ingestion, evaluation, or
  low-level components, but the SabiPass layer model should remain in charge.
- Redis-dependent libraries should be deferred unless the architecture changes.
  Use `cachetools` and `diskcache` for MVP-local caching instead.

## Highest-Risk Manual Implementations

These are the places where hand-rolled code is most likely to harm correctness
or production reliability:

1. `app/services/bkt_engine.py`: fixed mastery output undermines adaptive
   learning. Use `pyBKT` before treating mastery as meaningful.
2. `app/rag/embeddings.py`: hash embeddings make retrieval tests pass without
   proving semantic retrieval quality. Replace with real embeddings before
   evaluating RAG quality.
3. `app/services/strategy/concept_normalizer.py`: token overlap will miss many
   Pidgin, typo, and paraphrase cases. Add embedding/classifier support while
   keeping strict alias matching first.
4. `app/math/*.py`: math verification should not be invented from scratch.
   Use SymPy-centered tooling with timeouts and explicit low-confidence states.
5. `app/observability/*.py`: custom trace buffers are easy to get wrong under
   concurrency. Use standard logging/tracing libraries and keep the existing
   `SystemTrace` schema as the domain event.

## Research Sources

- pyBKT: https://github.com/CAHLR/pyBKT
- pyKT: https://github.com/pykt-team/pykt-toolkit
- River: https://github.com/online-ml/river
- Sentence Transformers: https://www.sbert.net/
- Hugging Face Sentence Transformers overview: https://huggingface.co/docs/hub/sentence-transformers
- FastEmbed: https://qdrant.github.io/fastembed/
- spaCy pipelines: https://spacy.io/usage/processing-pipelines
- SymPy: https://docs.sympy.org/latest/index.html
- Math-Verify: https://github.com/huggingface/Math-Verify
- Chroma: https://docs.trychroma.com/docs/overview/introduction
- Qdrant Python client: https://python-client.qdrant.tech/
- Haystack: https://docs.haystack.deepset.ai/docs/intro
- LlamaIndex: https://docs.llamaindex.ai/
- Ragas: https://docs.ragas.io/en/stable/tutorials/rag/
- DeepEval: https://deepeval.com/docs/introduction
- SetFit: https://huggingface.co/docs/setfit/index
- Rasa intents/entities: https://rasa.com/docs/reference/primitives/intents-and-entities/
- orjson: https://github.com/ijl/orjson
- uvloop: https://github.com/MagicStack/uvloop
- pydantic-settings: https://pydantic.dev/docs/validation/2.12/concepts/pydantic_settings/
- SlowAPI: https://slowapi.readthedocs.io/
- HTTPX: https://www.python-httpx.org/
- cachetools: https://cachetools.readthedocs.io/
- diskcache: https://pypi.org/project/diskcache/
- structlog: https://www.structlog.org/en/stable/index.html
- OpenTelemetry Python: https://opentelemetry.io/docs/languages/python/
- OpenTelemetry FastAPI instrumentation: https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/fastapi/fastapi.html
- Evidently: https://docs.evidentlyai.com/docs/library/overview
- LiteLLM: https://docs.litellm.ai/
- Instructor with LiteLLM: https://python.useinstructor.com/integrations/litellm/
- Guardrails AI: https://guardrailsai.com/guardrails/docs/concepts/guard
- Tenacity: https://tenacity.readthedocs.io/en/stable/
- aiobreaker: https://aiobreaker.netlify.app/index.html
- Docling: https://www.docling.ai/
- PyMuPDF: https://pymupdf.readthedocs.io/
- PyMuPDF4LLM: https://github.com/pymupdf/pymupdf4llm
- msgspec: https://github.com/jcrist/msgspec
- Hypothesis: https://github.com/HypothesisWorks/hypothesis
- Factory Boy: https://factoryboy.readthedocs.io/
- pytest-factoryboy: https://pytest-factoryboy.readthedocs.io/en/latest/
- Faker: https://faker.readthedocs.io/
- pytest-benchmark: https://pytest-benchmark.readthedocs.io/
- responses: https://pypi.org/project/responses/
- RESPX: https://lundberg.github.io/respx/guide/
- APScheduler: https://apscheduler.com/
