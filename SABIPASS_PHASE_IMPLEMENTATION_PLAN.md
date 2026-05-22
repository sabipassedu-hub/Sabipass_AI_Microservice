# SabiPass Phase Implementation Plan

This is the live implementation checklist for the Python AI microservice.
Every Codex session must update this file before finishing.

Status markers:
- `[x]` complete
- `[~]` in progress
- `[ ]` not started
- `[!]` blocked

## Session Notes Hygiene

- Keep `SABIPASS_PHASE_IMPLEMENTATION_PLAN.md` at or below 300 lines.
- Keep `Latest Session Notes` at or below 600 characters.
- Move previous session notes into `SESSIONS_LOG.md` before writing new notes.
- Keep only the current session summary in this file.

## Session Entry Ritual

- [x] Read `docs/ARCHITECTURE.md`.
- [x] Read `docs/ENGINEERING_GUIDELINES.md`.
- [x] Read `CODEX_MASTER_DIRECTIVE.md`.
- [x] Confirm original test suite still passes after edits.

## Phase 0 - Foundation Decisions

- [x] Replace architecture and context docs with 11-layer baseline.
- [x] Create structural stubs for Layer 2, 4, 8, 10, and 11 packages.
- [x] Create initial empty concept registry and fallback summary shells.
- [x] Create `CODEX_MASTER_DIRECTIVE.md` as director-level decision source.
- [x] Add LiteLLM dependency to `requirements.txt`.
- [x] Keep architecture aligned with MVP directive where it supersedes older scale assumptions.

## Phase 1 - Contracts And Demo Surface

- [x] Create `NODE_JS_CONTRACT.md` with exact request/response examples.
- [x] Add tier and efficiency-mode fields to the request contract and schema.
- [x] Add schema tests for tier history limits and zero-pass `correct_answer` rules.
- [x] Create `streamlit_test/` demo interface that calls the FastAPI endpoint.
- [x] Document local demo run commands in `README.md`.

## Phase 2 - Data Foundation

- [x] Populate `data/processed/concept_registry.json` with WAEC/JAMB math topics.
- [x] Add Pidgin aliases, common shortforms, and misspellings to the registry.
- [x] Populate `data/processed/fallback/general_mathematics_v1_summary.json`.
- [x] Add validation tests for registry shape and fallback summary shape.
- [x] Create `data/raw/mock/` and mock parser input format.

## Phase 3 - Layer 2 Strategy Engine

- [x] Implement `app/services/strategy/complexity_scorer.py`.
- [x] Implement `app/services/strategy/intent_parser.py`.
- [x] Implement `app/services/strategy/concept_normalizer.py`.
- [x] Implement `app/schemas/strategy.py`.
- [x] Implement `app/services/strategy/compiler.py`.
- [x] Add unit tests for English and Pidgin routing.

## Phase 4 - Provider-Agnostic LLM Routing

- [x] Add provider-agnostic model router stub around LiteLLM-only policy.
- [x] Add LLM executor stub around LiteLLM-only policy.
- [x] Implement env-driven model selection:
  `TIER_FREE_MODEL`, `TIER_PREMIUM_MODEL`, `EFFICIENCY_MODE_MODEL`.
- [x] Implement history limits:
  `TIER_FREE_MAX_HISTORY_TURNS`, `TIER_PREMIUM_MAX_HISTORY_TURNS`.
- [x] Add tests that no direct provider SDK is imported by LLM execution code.

## Phase 5 - RAG Precision And Fallback

- [x] Implement RAG router precision mode from StateStrategy.
- [x] Implement fallback summary loader.
- [x] Add retrieval tests for source tags, filters, and fallback behavior.
- [x] Wire concept normalization output into RAG query construction.

## Phase 6 - Mock Ingestion Pipeline

- [x] Create mock loader for `data/raw/mock/`.
- [x] Adapt ingestion pipeline so real PDF parsing can replace only the loader.
- [x] Validate processed question metadata.
- [x] Seed Chroma from mock processed data.

## Phase 7 - End-To-End Demo

- [x] Wire `neural_chat.py` through Layer 2, RAG, model router, and LLM executor.
- [x] Return pedagogically appropriate responses for English and Pidgin WAEC math prompts.
- [x] Verify free, premium, and efficiency-mode routing in Streamlit.
- [x] Run full test suite.

## Out Of Scope Until After Demo

- [ ] Kubernetes.
- [ ] Multi-pod registry.
- [ ] Redis.
- [ ] Full evaluation bench and deployment gate.
- [ ] Production security hardening.
- [ ] Full observability trace flushing.
- [ ] Human governance beyond stubs.
- [ ] WhatsApp or USSD integration.
- [ ] Python direct Supabase integration.

## Latest Session Notes

- Fixed tutoring control flow so known learning state anchors valid math follow-ups instead of falling into topic clarification.
- Added strict LLM response contracts and structured local tutoring fallbacks for explanation, practice, and correction.
- Verified full suite with temp pytest cache override: 187 passed.
