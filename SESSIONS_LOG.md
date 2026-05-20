# SabiPass Session Log

Historical session notes live here so `SABIPASS_PHASE_IMPLEMENTATION_PLAN.md`
stays short, current, and fast to read.

## 2026-05-19 - MVP Context Alignment

- Read `docs/ARCHITECTURE.md`, `docs/ENGINEERING_GUIDELINES.md`, `SABIPASS_CONTEXT.md`, and `CODEX_MASTER_DIRECTIVE.md`.
- Completed the Phase 0 MVP-alignment item by updating `SABIPASS_CONTEXT.md` from stale 1M+/12-step assumptions to the master directive's 100,000-user, single-server, 11-layer MVP scope.
- Added doc regression tests for the context scale target and pipeline layer count.
- Verified full test suite: 28 passed.

## 2026-05-19 - Session Notes Hygiene

- Added session-note hygiene rules: plan <=300 lines, latest notes <=600 characters, and prior notes move to `SESSIONS_LOG.md`.
- Created `SESSIONS_LOG.md` and archived the previous MVP context-alignment notes.
- Verified full test suite: 32 passed.

## 2026-05-19 - Streamlit Demo Surface

- Created `streamlit_test/` demo with tier selector, efficiency toggle, student input, response display, and canonical Node-shaped payload helper.
- Documented FastAPI/Streamlit demo commands in `README.md` and added the Streamlit dependency.
- Added focused demo/README tests; verified full suite: 36 passed.

## 2026-05-19 - Concept Registry Content

- Populated `data/processed/concept_registry.json` with canonical WAEC/JAMB mathematics topics.
- Added Pidgin aliases, common shortforms, and misspellings mapped to canonical concept keys.
- Added focused registry content tests; verified full suite: 39 passed.

## 2026-05-19 - Fallback Summary And Data Shapes

- Populated the general mathematics fallback summary with foundational WAEC/JAMB tutoring guidance under the 600-token cap.
- Added data-shape tests for registry entries, aliases, fallback hierarchy, and fallback summary shape.
- Verified full suite: 44 passed.

## 2026-05-19 - Mock Input And Complexity Scoring

- Created `data/raw/mock/` with a WAEC mathematics mock PDF-parse JSON input format and shape tests.
- Implemented deterministic 0-5 Layer 2 complexity scoring with Pidgin/frustration safeguards.
- Verified full suite: 51 passed.

## 2026-05-19 - Intent And Concept Normalization

- Implemented rule-based Layer 2 intent parsing with English/Pidgin explanation, correction, answer-request, and escape-valve signals.
- Implemented registry-snapshot concept normalization with strict, semantic, degraded, and clarification outcomes.
- Verified full suite: 63 passed.

## 2026-05-19 - Strategy Schema And Compiler

- Implemented immutable Layer 2 `StateStrategy` schema with RAG, pedagogy, and model strategy sub-objects.
- Implemented `compile_state_strategy` orchestration over complexity, intent, and concept normalization without RAG/LLM execution.
- Verified full suite: 70 passed.

## 2026-05-19 - English/Pidgin Routing And Model Router Stub

- Added English and Pidgin Layer 2 routing regression tests for equivalent linear-equation prompts.
- Implemented provider-agnostic LiteLLM model-route stub returning tier/efficiency env-var route metadata without env lookup.
- Verified full suite: 76 passed.

## 2026-05-19 - LiteLLM Executor And Env Models

- Completed the Phase 4 LiteLLM executor stub with typed request/result objects and an injectable completion callable for tests.
- Implemented env-driven model selection for `TIER_FREE_MODEL`, `TIER_PREMIUM_MODEL`, and `EFFICIENCY_MODE_MODEL`.
- Added `docs/DATA_ANALYST_RAG_INPUT_SCHEMA.md`.
- Verified full suite: 80 passed.

## 2026-05-19 - History Limits And SDK Guard

- Added explicit `max_history_turns` to `ModelRoute`, sourced from `TIER_FREE_MAX_HISTORY_TURNS` and `TIER_PREMIUM_MAX_HISTORY_TURNS`; efficiency mode remains zero-history.
- Added an AST guard test ensuring LLM execution imports LiteLLM and no direct provider SDKs.
- Verified full suite: 82 passed.

## 2026-05-19 - RAG Precision And Fallback Loader

- Implemented Phase 5 precision RAG routing from `StateStrategy`, embedding only the canonical concept key and passing strategy filters/top_k into Chroma retrieval.
- Added cached fallback summary loading with shape, token-count, and 600-token validation; fallback mode performs no vector search.
- Verified full suite: 85 passed.

## 2026-05-19 - RAG Retrieval Tests And Query Construction

- Added RAG retrieval tests covering real Chroma metadata filters, stable source tags, fallback no-vector behavior, and Pidgin-to-canonical query construction.
- Added `RagQuery` construction from `StateStrategy.normalized_concept` and Chroma `$and` filter handling for multi-field filters.
- Verified full suite: 87 passed.

## 2026-05-19 - Mock Loader And Pipeline

- Added typed ingestion document contracts plus a mock JSON loader for `data/raw/mock/`.
- Added a loader-injected ingestion pipeline so future real PDF parsing can swap only the loader callable.
- Added focused ingestion tests; verified full suite: 92 passed.

## 2026-05-19 - Ingestion Metadata And Chroma Seeding

- Added processed question metadata validation against canonical registry keys and required retrieval metadata fields.
- Added Chroma `exam_bank` seeding from validated mock records with deterministic local embeddings and source-tag-ready metadata.
- Added focused tests; verified full suite: 103 passed.

## 2026-05-19 - Neural Chat Pipeline Wiring

- Wired `neural_chat.py` through strategy compilation, RAG retrieval, model routing, and LiteLLM executor orchestration.
- Added tutor prompt/fallback logic for English and Pidgin WAEC math prompts.
- Added focused endpoint/service tests; verified full suite: 108 passed.

## 2026-05-20 - VC Readiness Hardening

- Added `.env`-aware settings defaults for Groq/LiteLLM model routing and history limits.
- Replaced runtime hash embeddings with FastEmbed, seeded all local demo Chroma collections, and added retrieval golden-set coverage.
- Added SymPy/math-verify grounding for surds and quadratic expressions; verified live API scenarios and full suite: 120 passed.
