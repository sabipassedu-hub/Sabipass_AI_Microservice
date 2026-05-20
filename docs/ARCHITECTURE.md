# SabiPass AI Microservice Architecture

SabiPass AI is the Python cognition service for a structured Nigerian exam tutoring platform. It is not a chat backend and not the Node.js product backend.

## Scope

Python owns tutoring cognition only: zero-pass evaluation, strategy compilation, RAG execution, deterministic math processing, tutor decisioning, controlled LLM execution, response packaging, observability traces, evaluation replay, governance queue ingestion, and registry snapshots.

Python must not own accounts, subscriptions, payments, persisted student sessions, Supabase student state, parent/school policy, moderation policy, or Teach First gate enforcement. Node.js sends already-authorized, already-gated requests.

## Public Endpoint

`POST /api/v1/neural/chat`

Boundary behavior:
- validate request schema;
- run zero-pass before any RAG/LLM;
- return `SabiNeuralResponse`;
- never perform disk I/O inside the request path except Chroma reads;
- never fetch missing student state from Supabase.

## Request Contract

Canonical request groups:
- `request_metadata`: `uuid_transaction_id`, `timestamp`, `device_latency_ms`
- `student_identity`: `student_db_id`, `tier`, `academic_scope`, `exam_target`
- `app_execution_mode`: `exam_prep | curriculum_coach | general_prompt | navigation_click`
- `cognitive_aptitude_profile`: regression/velocity, scaffolding, tolerance, decay fields
- `emotional_telemetry`: rage/caps/frustration/sentiment/focus fields
- `current_interaction_context`: `raw_whiteboard_input`, `topic_node`, last 3 history tokens, `errors_on_same_concept_space`
- `historical_mastery_map`: active weaknesses and passed topics

For zero-pass MCQ only, `current_interaction_context.correct_answer` is allowed when `app_execution_mode = exam_prep` and the selected input is `A-D`. It must be server-to-server only.

## Response Contract

`SabiNeuralResponse`:
- `request_id`
- `response_type`: `text_only | canvas_required | micro_clarification | zero_pass_response`
- `is_atomic`
- `tutor_conversational_text`
- optional `canvas_directive`
- optional `micro_rewards`
- optional `neural_sync_payload`
- `system_metadata`

Canvas render types remain only:
- `step_by_step_solution`
- `interactive_quiz_game`
- `split_view_doc`

Math disambiguation must use `response_type = micro_clarification` plus metadata, not a fourth render type.

## Layer 1: Request Lifecycle

Node.js owns transaction idempotency and must cache duplicate `uuid_transaction_id` responses with TTL. Python owns zero-pass interception:
- MCQ `A-D` in exam mode;
- navigation click mode;
- no RAG, no LLM, target under 40ms.

## Layer 2: Strategy Compilation

`app/services/strategy/compiler.py` creates immutable `StateStrategy`.

It runs local complexity scoring and intent parsing first, then concept normalization. LLM normalization is not in the Phase 3 critical path. Misses degrade to broad parent keys or micro-clarification.

StateStrategy includes:
- execution path;
- complexity score;
- normalized concept;
- normalization confidence/status;
- RAG strategy;
- pedagogy strategy;
- model strategy.

Downstream layers may execute strategy, not mutate it.

## Layer 3: RAG Retrieval

`app/services/rag_router.py` is the only service-level RAG entry. `app/rag/retriever.py` is the only low-level Chroma query utility.

Precision mode:
- select collection by strategy;
- apply metadata filters before vector search;
- query from canonical key, not raw user text;
- top_k 3, max 5;
- source-tag every hit.

Fallback mode:
- no vector search;
- load `data/processed/fallback/{concept_key}_summary.json`;
- max 600 tokens, foundational only.

Worked-solution chunks may be up to 600 tokens; total RAG budget may rise to 1200 tokens for verified worked solutions. Never truncate math; drop whole chunks.

## Layer 4: Math Engine

All math parsing, normalization, equivalence, and validation are non-LLM.

SymPy runs in a bounded process pool:
- `SYMPY_MAX_WORKERS`, default `max(1, CPU_CORES - 1)`;
- 100ms timeout;
- timeout kills work and triggers conceptual fallback.

Low-confidence math input returns micro-clarification and syncs pending clarification state to Node.

## Layer 5: Tutor Decision

Rule-based only. The LLM does not choose teaching mode.

Modes:
- Socratic
- Direct Instruction
- Remediation
- Direct Answer escape valve

Direct Answer requires verified grounding from exam bank, structured solution JSON, or SymPy. If unavailable, return a trust-preserving guided approach, not a hallucinated answer.

## Layer 6: LLM Execution

The LLM executes strategy only.

Paths:
- zero-pass: no LLM;
- grounded single-pass: formatter/explainer over trusted data;
- two-pass: structured plan then controlled response.

Quota priority:
1. final response generation;
2. reasoning compiler;
3. normalization fallback, disabled from Phase 3 critical path.

All structured output must use schema/function enforcement. Circuit breakers fall back safely.

## Layer 7: Packaging

`app/services/response_packager.py` validates and atomically packages full responses. Canvas/structured payloads remain atomic.

Python does not send two HTTP responses for one POST. Node/mobile may show a local processing skeleton while Python works. Streaming is allowed only for non-atomic `text_only`.

## Layer 8: Observability

Request completion appends `SystemTrace` to bounded memory. A FastAPI lifespan worker flushes JSONL batches outside the request path.

Trace buffer max size and flush threshold are env-configurable. Metrics are fire-and-forget to a sidecar.

## Layer 9: Evaluation Bench

Evaluation replay is deterministic:
- mocked/cached LLM only;
- real SymPy;
- isolated RAG directories per worker;
- fixed RNG;
- fail deployment on latency, fallback, format, hallucination, or normalization regressions.

`run_evaluation_gate.py` must be required before production deploy.

## Layer 10: Human Governance

Human review events are non-blocking. MVP uses bounded file-backed queue; production uses Redis.

Review actions: approve, correct, reject, add alias, flag content gap. No AI writes directly to registry assets.

## Layer 11: Registry Snapshot Stability

Requests read an immutable registry snapshot captured at entry. In-process pointer swap is valid only within one worker. Multi-pod production requires external shared registry storage plus polling and local atomic swaps.

## Data

Chroma collections:
- `exam_bank`
- `curriculum_vault`
- `analogy_sandbox`

Required metadata:
`subject`, `topic`, `difficulty`, `exam_type`, `academic_stage`, `has_worked_solution`, `year`.

Source tag format:
`src:v1;collection=...;source_type=...;doc_id=...;chunk_id=...;subject=...;topic=...;exam_type=...;academic_stage=...;year=...;has_worked_solution=...;rank=...`

## Phase Plan

Deprecated completed phases:
- Phase 1 API Contract Validation
- Phase 2 Pipeline Stabilization

Current Phase 3:
1. align schemas and docs;
2. seed concept registry and fallback summaries;
3. implement strategy compiler and concept normalization;
4. implement RAG precision/fallback router;
5. add retrieval evaluation gate.

Later phases:
- math engine hardening;
- tutor decision and LLM execution;
- packaging and observability;
- governance/evaluation;
- production multi-pod stability.
