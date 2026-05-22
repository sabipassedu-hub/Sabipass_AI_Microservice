# SabiPass AI System Repair Plan

This plan converts the current service into a VC-demo-safe system first, then layers in production behavior without broad rewrites. It follows the existing 11-layer architecture and the audit findings from the live execution, load, and deployment checks.

## Library Review

- Async safety: use Python/FastAPI threadpool boundaries for the current sync route, plus standard semaphores/locks for in-process coordination. AnyIO is already in the FastAPI stack and is suitable for later async route conversion, but Phase 1 does not need a route rewrite.
- Retries: use `tenacity`, already in `requirements.txt`, for bounded retry/backoff around LiteLLM calls.
- Rate limiting: SlowAPI/limits is a good FastAPI library for client-facing route limits, but Node.js owns product rate limits. For VC demo stability, start with internal model concurrency control instead of adding route-level throttling.
- Circuit breakers: `aiobreaker` is suitable for async service calls, but adding it before converting the model path to async would add little value. Phase 1 implements a small synchronous model circuit breaker at the integration point.
- Caching: `cachetools` and `diskcache` already exist in dependencies. Keep registry/fallback caches in memory for request safety; use DiskCache later only for explicit cross-process demo cache needs.
- Task queues: ARQ and Celery are high-quality queue options, but both require broker infrastructure for the useful production shape. Defer queues; VC demo response generation must stay synchronous and bounded.
- Observability: OpenTelemetry FastAPI instrumentation is already listed in dependencies and should be wired in Phase 6 with structured local traces.

## PHASE 1 - CRITICAL RUNTIME STABILITY

### Objective
Stop hanging requests, cap model concurrency, make LLM failures deterministic, and preserve a fast local fallback path.

### Problems It Solves
- 90s hanging requests during 100-concurrent audit load.
- Provider rate-limit and internal errors cascading into latency spikes.
- No model timeout wrapper, retry policy, or circuit breaker.

### Exact Files To Modify
- `app/core/config.py`
- `app/services/llm_executor.py`
- `app/services/tutor_engine.py`
- `tests/unit/services/test_llm_executor.py`
- `tests/unit/services/test_tutor_engine.py`

### Step-By-Step Implementation Plan
1. Add model execution settings: timeout seconds, max concurrent model calls, retry attempts, retry backoff, and circuit breaker thresholds.
2. Wrap LiteLLM execution in a bounded thread executor so one provider call cannot hang the request indefinitely.
3. Add a process-local semaphore to cap concurrent LLM calls per worker.
4. Add Tenacity retry for transient model errors with short exponential backoff.
5. Add a lightweight process-local circuit breaker that temporarily skips provider calls after repeated failures.
6. Preserve existing tutor fallback responses and expose precise fallback reasons in `system_metadata`.

### Libraries
- `tenacity`: already installed; used for short bounded retry/backoff. It does not violate architecture because it wraps only the central LiteLLM executor.
- No new dependency in this phase.

### Expected System Improvement
- Zero unbounded model waits.
- Provider overload degrades into local fallback instead of request timeout.
- Mean and p95 latency improve under concurrent load because calls fail fast when the model path is saturated or unhealthy.

## PHASE 2 - REQUEST PATH HARDENING

### Objective
Make malformed-but-schema-valid payloads safe and bounded.

### Problems It Solves
- Negative latency, invalid timestamps, empty IDs, huge arrays, huge prompts, and nonsense telemetry were accepted.
- Request path can spend CPU on payloads that should be rejected at validation.

### Exact Files To Modify
- `app/schemas/requests.py`
- `tests/unit/schemas/test_neural_chat_request.py`
- `tests/integration/test_invalid_payload.py`

### Step-By-Step Implementation Plan
1. Enforce transaction ID, timestamp shape, and non-negative latency.
2. Cap raw input length, history count/string length, weaknesses, passed topics, and telemetry arrays.
3. Normalize allowed low-cardinality signal fields.
4. Return deterministic 422 responses for invalid payloads.

### Libraries
- Pydantic v2 validators are already in use and are the right tool here.

### Expected System Improvement
- Reduced memory and CPU abuse.
- Predictable integration failures instead of runtime degradation.

## PHASE 3 - COMPUTE ISOLATION (LLM / SYMPY / RAG)

### Objective
Move expensive compute and I/O setup out of unsafe request-path behavior.

### Problems It Solves
- Chroma setup runs through request dependency.
- SymPy verification bypasses the bounded worker described in architecture.
- FastEmbed warmup depends on manual scripts.

### Exact Files To Modify
- `app/core/lifespan.py`
- `app/api/v1/routes/neural_chat.py`
- `app/math/sympy_worker.py`
- `app/services/math_verifier.py`
- `tests/unit/services/test_math_verifier.py`
- `tests/integration/test_neural_chat_pipeline.py`

### Step-By-Step Implementation Plan
1. Initialize Chroma collections once during lifespan and store in `app.state`.
2. Warm FastEmbed during explicit demo/ready startup mode, not every production boot.
3. Route quadratic verification through the bounded SymPy worker.
4. Fail closed to conceptual fallback on SymPy timeout.

### Libraries
- Use existing `concurrent.futures.ProcessPoolExecutor`; no new library needed.

### Expected System Improvement
- Less request-path I/O.
- Bounded CPU work.
- Lower first-request surprise latency in demo mode.

## PHASE 4 - CONCURRENCY + RATE CONTROL

### Objective
Prevent provider and local compute overload before it becomes user-visible.

### Problems It Solves
- Provider calls overwhelmed under 100 concurrent audit requests.
- No backpressure.
- No route-level emergency guard.

### Exact Files To Modify
- `app/core/config.py`
- `app/api/v1/routes/neural_chat.py`
- `app/services/llm_executor.py`
- `app/services/runtime_limits.py`
- `tests/unit/services/test_runtime_limits.py`

### Step-By-Step Implementation Plan
1. Add request admission settings for demo mode.
2. Implement per-worker token bucket or bounded semaphore guard.
3. Return safe tutoring fallback, not raw 503, when model capacity is exhausted.
4. Optionally add SlowAPI only if Node.js/product-level limits are not available for the demo.

### Libraries
- Prefer internal semaphore/token bucket for VC demo.
- SlowAPI/limits is acceptable later for external route limits.

### Expected System Improvement
- Stable 100-concurrent behavior with bounded p95 latency.
- No provider stampede.

## PHASE 5 - FALLBACK + DETERMINISTIC RESPONSES

### Objective
Make common demo responses deterministic and high-quality without depending on the LLM.

### Problems It Solves
- Generic fallback text is too vague for a VC demo.
- Zero-pass MCQ is not implemented.
- Algebra, surds, and RAG-miss cases need reliable responses.

### Exact Files To Modify
- `app/api/v1/routes/neural_chat.py`
- `app/services/zero_pass.py`
- `app/services/tutor_engine.py`
- `app/services/math_verifier.py`
- `tests/integration/test_neural_chat.py`
- `tests/unit/services/test_zero_pass.py`

### Step-By-Step Implementation Plan
1. Implement Layer 1 zero-pass before BKT/RAG/LLM.
2. Add deterministic templates for linear equations, quadratics, surds, and broad math fallback.
3. Make fallback reasons explicit and stable.
4. Keep response shape atomic and Node-compatible.

### Libraries
- Existing SymPy for supported math.
- No new dependency needed.

### Expected System Improvement
- Demo can survive provider outage.
- Common student flows return useful answers consistently.

## PHASE 6 - OBSERVABILITY + TRACEABILITY

### Objective
Make every request explainable after the fact.

### Problems It Solves
- No real traces, metrics, or structured logs.
- Fallback and timeout causes are not aggregated.

### Exact Files To Modify
- `app/observability/trace_buffer.py`
- `app/observability/flush_worker.py`
- `app/observability/metrics.py`
- `app/schemas/traces.py`
- `app/core/lifespan.py`
- `app/api/v1/routes/neural_chat.py`

### Step-By-Step Implementation Plan
1. Implement bounded in-memory trace buffer.
2. Add non-blocking request trace append.
3. Add lifespan flush worker for JSONL demo logs.
4. Wire OpenTelemetry FastAPI instrumentation in app creation.

### Libraries
- OpenTelemetry FastAPI instrumentation already exists in dependencies and matches the architecture.

### Expected System Improvement
- Production debugging has request IDs, latency, model status, RAG status, and fallback reasons.

## PHASE 7 - DEPLOYMENT + ENVIRONMENT READINESS

### Objective
Make a clean checkout deployable and verifiable.

### Problems It Solves
- Clean tracked repo cannot seed demo data.
- No health/readiness endpoints.
- No Docker/deploy manifest or environment example.

### Exact Files To Modify
- `.env.example`
- `Dockerfile`
- `app/api/v1/routes/health.py`
- `main.py`
- `README.md`
- `data/raw/mock/waec_mathematics_mock_parse.json` or an equivalent tracked processed seed path

### Step-By-Step Implementation Plan
1. Add `.env.example`.
2. Add health and readiness endpoints.
3. Ensure demo seed data needed for VC mode is tracked or switch seeding to tracked processed data.
4. Add a minimal Dockerfile and production start command.
5. Add CI-safe pytest command using temp/cache outside repo on Windows.

### Libraries
- No new runtime library needed.

### Expected System Improvement
- Clean checkout can run.
- Deployment can fail fast before serving traffic.

## PHASE 8 - DEMO MODE + VC SAFETY LAYER

### Objective
Make the investor demo predictable even during provider failures.

### Problems It Solves
- Streamlit can time out at 20s under load.
- Demo depends on live provider success.
- No scripted safety mode.

### Exact Files To Modify
- `app/core/config.py`
- `app/services/tutor_engine.py`
- `streamlit_test/app.py`
- `README.md`
- `tests/unit/demo/test_streamlit_demo.py`

### Step-By-Step Implementation Plan
1. Add `SABI_DEMO_MODE` with deterministic model-bypass for supported demo prompts.
2. Keep live model path available but non-blocking.
3. Surface fallback-safe status in Streamlit without exposing raw internals to students.
4. Add demo smoke script for the VC route matrix.

### Libraries
- No new dependency needed.

### Expected System Improvement
- Investor demo works offline or under provider rate pressure.
- Student-visible behavior remains coherent.
