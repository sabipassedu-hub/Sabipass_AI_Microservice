# SabiPass AI Context

Python scope: AI tutoring microservice only. Node.js owns auth, subscriptions, policy, idempotency, moderation, Teach First gating, persistence, and Supabase state.

Current status:
- Phase 1 API Contract Validation: complete, deprecated as active work.
- Phase 2 Pipeline Stabilization: complete, deprecated as active work.
- Phase 3 Vector Retrieval: ready, but blocked by schema alignment, concept registry, fallback summaries, and Layer 2 strategy modules.

Target scale: 100,000 users. Not concurrent. MVP deployment is a correctly
tuned single-server service for Nigeria launch, WAEC and JAMB first.

Pipeline:
1. Node state assembly and idempotency.
2. Python zero-pass interceptor.
3. Strategy compilation.
4. RAG strategy and retrieval.
5. Math input processing.
6. Tutor decision.
7. LLM execution.
8. Response packaging.
9. Observability.
10. Human governance.
11. Registry snapshot stability.

Critical decisions:
- `concept_registry.json` lives in `data/processed/`, not `app/core/`.
- Strategy modules live in `app/services/strategy/`.
- Fallback summaries live in `data/processed/fallback/`.
- SymPy verification is separate from tutor engine.
- FastAPI background workers use lifespan, not deprecated startup events.
- LLM normalization is removed from Phase 3 critical path.
- Pidgin intent and escape phrases are first-class routing signals.
- Direct-answer mode cannot use free generation.
- Canvas has exactly three render types; micro-clarification is a response type, not a new render type.
- No Kubernetes, multi-pod registry, or Redis is in MVP scope.

Immediate Phase 3 order:
1. update docs/schema tests;
2. add concept registry and fallback specs;
3. implement strategy compiler and Pidgin intent parser;
4. implement concept normalizer over registry snapshot;
5. implement RAG router precision/fallback with source tags.
