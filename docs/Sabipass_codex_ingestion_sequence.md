████████████████████████████████████████████████████████████████████████████
█                                                                          █
█   SABIPASS AI — CODEX 5.5 INGESTION SEQUENCE v2.0 (REBUILT)             █
█   Prepared by: Claude — Lead Reviewer + Bottleneck Analyst               █
█   Version: Post-11-Layer Architecture Review                             █
█   Total: 1 Master Prompt + 11 Chunks + 1 Final Synthesis Trigger         █
█                                                                          █
█   SOURCE LEGEND:                                                         █
█     [C]   = Claude session (primary build history)                       █
█     [GPT] = ChatGPT architectural design (Layers 1–11)                  █
█     [G]   = Google AI enterprise research compilation                    █
█     [F]   = Founder strategic input                                      █
█     [ALL] = Confirmed across all sources                                 █
█     [SIM] = Identified in simulation analysis (Claude review)            █
█     [FIX] = Optional fix — NOT mandatory. Codex is final authority.      █
█                                                                          █
████████████████████████████████████████████████████████████████████████████

════════════════════════════════════════════════════════════════════════════
▶ MASTER STARTING PROMPT — SEND THIS FIRST TO CODEX 5.5
════════════════════════════════════════════════════════════════════════════

COPY AND SEND THIS EXACTLY TO CODEX 5.5 BEFORE ANY CHUNK:

───────────────────────────────────────────────────────────────────────────
You are Codex 5.5 operating at highest intelligence level.

You are being loaded with full architectural context for the SabiPass AI
Python microservice system in 11 structured chunks, delivered sequentially.

This document was reviewed by a senior AI backend deployment engineer with
expertise in production systems at 100k to 1M user scale, Kubernetes,
CI/CD pipelines, and hidden bug detection. Bottlenecks have been
identified across all 11 architectural layers. Optional fixes are flagged
with [FIX]. You are the final authority — you decide what to accept,
reject, or refine.

You are responsible for the Python AI microservice ONLY.
The Node.js backend is NOT your responsibility.

DO NOT generate any output, architecture, or conclusions yet.
DO NOT summarize. DO NOT suggest anything. DO NOT ask questions.

Your ONLY task during ingestion is to:
  → read each chunk
  → store it internally
  → organize it against what you already hold

Each chunk is labeled CHUNK [N] OF 11.
You must wait until you receive the exact instruction:
  👉 "BEGIN ARCHITECTURAL SYNTHESIS"

Only after that instruction should you:
  → accept or reject each optional fix
  → produce the final architectural synthesis
  → produce updated codebase file specifications
  → resolve all open questions where sufficient information exists

Until then, respond ONLY with:
  "Context received. Awaiting Chunk [N+1] of 11."

Acknowledge this instruction now.
───────────────────────────────────────────────────────────────────────────


════════════════════════════════════════════════════════════════════════════
▶ CHUNK 1 OF 11 — SYSTEM OVERVIEW + TEAM + PHASE STATUS
════════════════════════════════════════════════════════════════════════════

--- CHUNK 1 OF 11 | DOMAIN: SYSTEM OVERVIEW ---

WHAT SABIPASS IS
[ALL] SabiPass is a scalable, real-time AI Personalized SaaS Tutoring
Platform. NOT a chat interface. A full structured learning system:
  AI tutoring (LLM two-pass), RAG retrieval, BKT student modeling,
  Canvas UI delivery, Gamification.

CORE POSITIONING: "Best Socratic tutor in Nigeria" [GPT]
CORE PURPOSE: Replace hallucinating AI tools with a trusted, exam-focused
  tutor that teaches before it solves, adapts per student, evolves over time.

TARGET SCALE: 1,000,000+ active users
GEOGRAPHY: Nigeria exclusively at launch
USERS: Primary=Students (JSS1–University), Secondary=Parents,
        Tertiary=Schools

STUDENT SEGMENTS
  primary_5 and below / JSS1–JSS3 / SS1–SS3 / University / A-Level

EXAM PRIORITY: WAEC (launch) → JAMB → NECO → GCE/Post-UTME/A-Levels
               → University exams

TEAM (Python microservice focus — sabipass-ai/ repo)
  Wisdom       → Python AI Microservice (this repo)
  Mishael      → Node.js Core App (separate repo)
  Frankly      → Data scraping and OCR (data/raw/ provider)
  React dev    → Frontend (Expo) + port-3000 backend API

SUBSCRIPTION TIERS (CONFIRMED NAIRA)
  Freemium         → Limited queries, ad-supported
  1000/month       → Text only, JSS, no photo, no voice
  5000/month       → Photo, TTS audio, SS3/WAEC prep
  10000/month      → Voice, mock analysis, A-Level/UTME

PHASE STATUS
  Phase 1 — API Contract Validation     → COMPLETE
  Phase 2 — Pipeline Stabilization      → COMPLETE
    2 integration tests GREEN
    schemas verified: requests.py + responses.py
    BKT → RAG → Tutor pipeline stubbed and wired
  Phase 3 — Vector Retrieval            → READY TO BEGIN
  Phase 4+ → see SABIPASS_PHASE_IMPLEMENTATION_PLAN.md

--- END CHUNK 1 OF 11 ---


════════════════════════════════════════════════════════════════════════════
▶ CHUNK 2 OF 11 — PRODUCT FEATURES
════════════════════════════════════════════════════════════════════════════

--- CHUNK 2 OF 11 | DOMAIN: PRODUCT FEATURES ---

TEACH FIRST, SOLVE SECOND (Node.js gated — not Python's responsibility)
[G][F] Stage 1: Socratic guide, formula breakdown, answer BLOCKED
       Stage 2: Unlocks after student passes comprehension check
       Gate is enforced by Node.js. Python receives already-gated requests.

DYNAMIC HINT TIERING [G]
  Tier 1: Restate core rule / definition
  Tier 2: Break formula into component parts
  Tier 3: Set up calculation step, student completes arithmetic only

PROACTIVE MISCONCEPTION INTERCEPTION [G]
  Detects known common wrong answers, targets underlying rule confusion

COGNITIVE SCAFFOLDING [G]
  Complex problems split into sub-tasks. Next step locked until current
  building block is mastered.

PERSONALIZATION [ALL]
  Adaptive study plans per student, weak area targeting, BKT per concept
  Learning velocity, knowledge decay, emotional telemetry

CANVAS UI (3 confirmed render types) [ALL]
  step_by_step_solution / interactive_quiz_game / split_view_doc
  API returns parameter flags ONLY — assets load from device storage

GAMIFICATION [ALL]
  XP, streak tracking, streak shield, fireworks_gold, streak_shield_protect
  Loss aversion safetynet, operant conditioning rewards

VOICE (gated 5000+ tiers) [F]
  On-device STT/TTS only, never server-side audio

HOMEWORK SOLVING (gated 5000+ tiers) [F]
  Vision AI, client-side compression < 200KB, Teach First gate enforced

CONTENT MODERATION [F][G]
  Filter layer between Node.js and AI service

EXISTING FRONTEND ENDPOINTS (from repo analysis) [C]
  POST /explain, POST /fromDocument, POST /fromYoutube,
  GET /voice, GET /questions, GET /questions/random

--- END CHUNK 2 OF 11 ---


════════════════════════════════════════════════════════════════════════════
▶ CHUNK 3 OF 11 — VERIFIED SCHEMAS + PIPELINE CONTRACT
════════════════════════════════════════════════════════════════════════════

--- CHUNK 3 OF 11 | DOMAIN: SCHEMAS + PIPELINE CONTRACT ---

REQUEST SCHEMA (requests.py) — VERIFIED AND LOCKED [C]
  request_metadata: uuid_transaction_id, timestamp (ISO-8601),
    device_latency_ms
  student_identity: student_db_id (Supabase UUID), tier (free|premium_plus),
    academic_scope, exam_target,
    app_execution_mode (exam_prep|curriculum_coach|general_prompt)
  cognitive_aptitude_profile: regression_slope (0.0–1.0),
    scaffolding_flag (high|low), complexity_tolerance,
    knowledge_decay_params
  emotional_telemetry: rage_clicks array, caps_lock_aggression array,
    sentiment_trends, latency_focus_integrity
  current_interaction_context: raw_whiteboard_input (string),
    topic_node (string), history_tokens (last 3 turns ONLY),
    errors_on_same_concept_space (integer — PRIMARY BKT SIGNAL)
  historical_mastery_map: active_weakness_arrays, passed_topics_arrays

[SIM] SCHEMA GAP: Zero-pass MCQ evaluation requires correct_answer field.
  Currently NO correct_answer field exists in schema.
  Without it, Python cannot evaluate MCQ locally in zero-pass mode.
[FIX — OPTIONAL] Add correct_answer to current_interaction_context,
  scoped only when app_execution_mode = "exam_prep". Codex to decide.

RESPONSE SCHEMA (responses.py) — VERIFIED AND LOCKED [C]
  CanvasDirective: render_type (Literal 3 values), meta dict, layout_slots
  MicroRewards: animation_flag, praise_tag, xp_value
  NeuralSyncPayload: updated_bkt_mastery, learning_velocity,
    updated_weakness_array (returned to Node.js for DB caching)
  SabiNeuralResponse (MASTER ENVELOPE):
    request_id, response_type (text_only|canvas_required|
    micro_clarification|zero_pass_response), is_atomic (bool),
    tutor_conversational_text, canvas_directive (optional),
    micro_rewards (optional), neural_sync_payload (optional),
    system_metadata

PIPELINE EXECUTION ORDER [C][GPT][G]
  [Request] →
  Layer 1: Node.js State Assembly + Idempotency Guard →
  [POST /api/v1/neural/chat] →
  Layer 1 (Python): Zero-Pass Interceptor →
  Layer 2: Strategy Compilation Engine →
  Layer 3: RAG Strategy + Context Retrieval →
  Layer 4: Math Input Processing + SymPy Validation →
  Layer 5: Tutor Decision Engine →
  Layer 6: LLM Execution Engine →
  Layer 7: Response Packaging + Atomic Delivery →
  [Response to Node.js]

  BACKGROUND (non-blocking, outside request path):
  Layer 8: Observability + Auto-Improvement Loop
  Layer 9: Continuous Evaluation Bench (CI/CD gate)
  Layer 10: Human-in-the-Loop Governance
  Layer 11: Memory Access + Runtime Stability

--- END CHUNK 3 OF 11 ---


════════════════════════════════════════════════════════════════════════════
▶ CHUNK 4 OF 11 — LAYER 1: REQUEST LIFECYCLE + LAYER 2: STRATEGY ENGINE
════════════════════════════════════════════════════════════════════════════

--- CHUNK 4 OF 11 | DOMAIN: LAYERS 1–2 ---

━━━ LAYER 1: REQUEST LIFECYCLE ━━━

NODE.JS PAYLOAD ASSEMBLY (not Python's code — defines what Python receives)
[GPT][G] Collects: user_input_text, app_execution_mode, canvas_state,
  transaction_id (UUID from device), client_latency_ms,
  bkt_mastery_snapshot, known_weaknesses, learning_behavior_profile,
  recent_interaction_summary (last 3 turns)
  Payload weight budget:
    student_identity < 100 bytes / cognitive_state < 200 bytes
    behavioral_metrics < 150 bytes / interaction_context < 1.2KB
  NO full chat history / NO raw textbook content

IDEMPOTENCY GUARD (Node.js enforced) [GPT][G]
  Same transaction_id seen again → DO NOT forward, RETURN cached response
  Prevents: double submissions, duplicate BKT updates, race conditions

[SIM] BN-11: Idempotency cache has no TTL → memory leak at scale
[FIX — OPTIONAL] Define TTL for transaction_id cache (e.g., 5 minutes)

PYTHON ZERO-PASS INTERCEPTOR (main.py / API gateway) [GPT][G]
  Trigger A: input in ["A","B","C","D"] AND mode = "exam_prep"
  Trigger B: app_execution_mode = "navigation_click"
  Behavior: evaluate answer locally, compute BKT update, return response
  Performance: < 40ms, $0 cost, no external calls
  Estimated traffic reduction: 60–80% of high-frequency requests

[SIM] BN-03: Zero-pass needs correct_answer in payload — not in schema yet
[FIX — OPTIONAL] See schema gap fix in Chunk 3

━━━ LAYER 2: STRATEGY COMPILATION ENGINE ━━━

POSITION: After Zero-Pass, before RAG
CEILING: < 150ms total — hard constraint, no exceptions

STATE STRATEGY OBJECT (immutable, created once) [GPT][G]
  execution_path: zero_pass | single_pass | two_pass
  complexity_score: 0–5
  normalized_concept: canonical curriculum key
  normalization_confidence: 0.0–1.0
  normalization_status: strict | semantic | degraded
  rag_strategy: { target_collection, filters }
  pedagogy_strategy: { teaching_mode, response_format }
  model_strategy: { use_psychologist, primary_model, fallback_model }
  HARD RULES: No mutation after creation. No downstream overrides.

NON-BLOCKING PARALLEL EXECUTION [GPT][G]
  Step 1 (parallel, fully local, no network, < 100ms):
    Complexity Scoring Engine + Intent Parser
  Step 2 (bounded, fail-fast, < 150ms total):
    Concept Normalization Engine

COMPLEXITY SCORING MATRIX [GPT][G]
  attempt_count >= 2    → +2
  frustration detected  → +1
  deteriorating trend   → +2
  intent = explanation  → +2 (keywords: why, how, explain, prove)
  math symbols present  → +1
  Routing: 0–1 → single_pass / 2–3 → adaptive / ≥3 → two_pass

[SIM] BN-05: Keyword matching fails on Nigerian Pidgin
  "wetin make am change sign" → no keyword match → score=0 → single_pass
  Real student language degrades routing accuracy severely.
[FIX — OPTIONAL] Extend intent keywords with Pidgin signals:
  "abeg", "wetin", "how e dey work", "make I understand"
  Codex to propose canonical Pidgin signal list.

CONCEPT NORMALIZATION ENGINE [GPT][G]
  Tier 1: Dictionary match (0ms) → concept_registry.json
  Tier 2: Semantic similarity (embedding-based)
  Tier 2.5: LLM fallback (strictly bounded ≤ 150ms)
  Failure: confidence < 0.85 OR timeout →
    normalized_concept = "broad_parent_key"
    normalization_status = "degraded"

[SIM] BN-02: Free Gemini rate limit (~60 req/min) shared across ALL uses:
  Layer 2 Tier 2.5 + Layer 6 Pass 1 + Layer 6 Pass 2 + ingestion tagger.
  Even 10 concurrent users causes cascading timeouts in normalization.
[FIX — OPTIONAL] Decouple normalization LLM from tutor LLM quota.
  Cache normalization results aggressively (concept key → canonical key).
  Consider normalization-only lightweight model separate from tutor model.

[SIM] BN-19: concept_registry.json does not exist yet
[FIX — OPTIONAL] Location: data/processed/concept_registry.json
  Initial content: WAEC mathematics syllabus topic list as canonical keys
  Version pattern: concept_registry_v1.0.json

INTENT PARSER (rule-based, no ML) [GPT][G]
  "why", "how" → explanation / "this is wrong" → correction
  "just tell me" → answer_request
  Output: { intent_type, urgency }

[SIM] BN-05 (continued): Escape phrases are English-only.
  Nigerian Pidgin equivalents not covered.
[FIX — OPTIONAL] See Layer 5 Pidgin fix in Chunk 6.

--- END CHUNK 4 OF 11 ---


════════════════════════════════════════════════════════════════════════════
▶ CHUNK 5 OF 11 — LAYER 3: RAG ENGINE + LAYER 4: MATH ENGINE
════════════════════════════════════════════════════════════════════════════

--- CHUNK 5 OF 11 | DOMAIN: LAYERS 3–4 ---

━━━ LAYER 3: RAG STRATEGY & CONTEXT RETRIEVAL ENGINE ━━━

POSITION: Pure executor of strategy from Layer 2. Does not interpret.

DUAL-MODE RETRIEVAL [GPT][G]
  Mode A (Precision): normalization_status = strict | semantic
  Mode B (Safe Fallback): normalization_status = degraded

MODE A — PRECISION RETRIEVAL [GPT][G]
  Step 1: Collection routing
    curriculum_coach → curriculum_vault / exam_prep → exam_bank
  Step 2: Metadata pre-filter BEFORE vector search
    Filter: { topic: canonical_key, academic_stage, exam_body }
    Eliminates ~80% noise before embedding scan
  Step 3: Query construction from canonical key (NEVER raw user text)
  Step 4: HNSW vector retrieval
    top_k = 3 (max 5), total ≤ 900 tokens, per chunk ≤ 300 tokens
  Step 5: Context sanitization (remove duplicates, normalize notation)
  Step 6: Format-aware packaging
    Math → steps + expressions / Accounting → tables / Theory → paragraphs
  Latency: ≤ 200ms

MODE B — SAFE FALLBACK (degraded) [GPT][G]
  NO vector search, NO embedding queries, NO similarity matching
  Load static pre-compiled curriculum summary block
  Examples: general_mathematics_v1_summary, intro_accounting_v1_summary
  Constraints: ≤ 600 tokens, max 2 blocks, foundational only
  Tag: { rag_mode: "fallback_static" }
  Latency: ≤ 50ms

[SIM] BN-04: Static fallback files DO NOT EXIST. No spec for:
  → File location in repository
  → Format (JSON? plain text? JSONL?)
  → Creation process (who creates? Gemini-assisted? manual?)
  → Maintenance ownership
  Mode B returns empty context without these files.
[FIX — OPTIONAL]
  Location: data/processed/fallback/{concept_key}_summary.json
  Format: { concept_key, summary_text, token_count, version }
  Creation: one-time Gemini-assisted generation script from
    Frankly's processed JSON before Phase 3 begins.

RETRIEVAL PRIORITY ORDER [C][GPT]
  1. has_worked_solution = true (HIGHEST)
  2. Past exam questions / 3. Concept explanations / 4. Analogies

[SIM] BN-18: 300-token per chunk limit vs "NEVER truncate math content"
  (Layer 4) are in direct conflict. Complete worked WAEC solutions
  routinely exceed 300 tokens.
[FIX — OPTIONAL] Raise chunk limit to 600 tokens when
  has_worked_solution = true. Total budget → ≤ 1200 tokens.
  Codex to define appropriate limits.

CHROMADB (confirmed) [ALL]
  3 collections: exam_bank, curriculum_vault, analogy_sandbox
  HNSW: cosine, construction_ef=200, M=16, search_ef=100
  retrieval_confidence = 1 − cosine_distance (clamped 0.0–1.0)

━━━ LAYER 4: MATHEMATICAL INPUT PROCESSING ━━━

CORE PRINCIPLE: NON-LLM for ALL parsing, normalization, validation.
               LLMs strictly forbidden in math parsing.

FRONTEND INPUT CONTRACT [GPT][G]
  Calculator-driven UI (WAEC/JAMB FX-991ES style)
  Frontend sends structured token object, NOT raw ambiguous strings:
  { type, raw_input, tokenized, ui_metadata: { input_mode, confidence_hint } }

DETERMINISTIC NORMALIZATION (< 1ms) [GPT][G]
  Implicit multiplication: 2x → 2*x
  Power normalization: x^2 → x**2
  Function mapping: sin(x) → sympy.sin(x)
  Ambiguous fractions flagged for confidence gate

CONFIDENCE GATE [GPT][G]
  HIGH > 0.85   → Proceed
  MEDIUM 0.6–0.85 → Soft warning, proceed
  LOW < 0.6     → HARD BLOCK → Emit micro-clarification canvas directive
    { render_type: "math_disambiguation", options: [visual A, visual B] }

SYMBOLIC EXECUTION (SymPy, sandboxed) [GPT][G]
  Sandboxed worker — NO raw Python eval
  Expression equivalence check, step validation
  NEVER truncate mathematical content — DROP entire chunk if token overflow

[SIM] BN-08: SymPy ProcessPoolExecutor max_workers unspecified.
  At 40k+ concurrent users with math inputs, unbound process pool
  saturates all CPU cores. Blocks event loop.
[FIX — OPTIONAL] Define SYMPY_MAX_WORKERS as environment variable.
  Default: CPU_CORES - 1 (reserve capacity for FastAPI event loop)

[SIM] BN-18 (continued): See Layer 3 token limit fix above.

[SIM] BN-MICRO-CLARIFICATION: Round-trip on unstable 3G creates
  state loss risk. If network drops during clarification wait,
  session state is lost.
[FIX — OPTIONAL] Include micro-clarification pending state in
  NeuralSyncPayload so Node.js can recover it on reconnect.

--- END CHUNK 5 OF 11 ---


════════════════════════════════════════════════════════════════════════════
▶ CHUNK 6 OF 11 — LAYER 5: TUTOR DECISION + LAYER 6: LLM EXECUTION
════════════════════════════════════════════════════════════════════════════

--- CHUNK 6 OF 11 | DOMAIN: LAYERS 5–6 ---

━━━ LAYER 5: TUTOR DECISION ENGINE ━━━

POSITION: After math validation, before LLM
PURPOSE: Governs HOW the system teaches. Does NOT generate content.
RULE: Mode selection is ALWAYS rule-based. Never delegated to LLM.

PEDAGOGICAL MODES [GPT][G]
  1. Socratic: attempt_count < 2, frustration low, mastery stable
  2. Direct Instruction: deep intent, complexity ≥ 3, first-time breakdown
  3. Remediation: mastery < 0.4, repeated incorrect, confusion signals
  4. Direct Answer (ESCAPE VALVE): explicit escape phrases OR
     emotional trend deteriorating OR attempt_count ≥ 2 no progress

CURRENT ESCAPE TRIGGER PHRASES [GPT][G]
  "just tell me", "I don't know", "give me answer"

[SIM] BN-05 (escape valve): Pidgin equivalents not covered:
  "abeg just show me", "e don do", "I no fit again", "help me sha"
[FIX — OPTIONAL] Pre-populate Pidgin escape phrase list.
  Continuously expand via Layer 8 observability data once live.

ESCAPE VALVE SAFETY ENFORCEMENT [GPT][G]
  When teaching_mode = direct_answer:
    disable_free_generation = true
    grounding_required = true
  Grounding hierarchy (must use ONE):
    1. Pre-verified past question solution (WAEC/JAMB exam_bank)
    2. Structured solution JSON (Frankly dataset)
    3. Verified symbolic computation (SymPy engine)
  FREE LLM GENERATION IS FORBIDDEN in direct_answer mode

[SIM] BN-10: At MVP, exam_bank may be incomplete.
  If student escapes on a topic not yet in knowledge base,
  grounding fails — system has no verified fallback answer.
[FIX — OPTIONAL] Define grounding-unavailable behavior:
  Return: "This specific solution isn't in my verified bank yet.
   Let me guide you through the approach instead."
  Fall back to Socratic — preserves trust without hallucination.

BKT-DRIVEN PERSONALIZATION [GPT][G]
  mastery > 0.8 → concise / 0.4–0.8 → balanced / < 0.4 → detailed + slow

RESPONSE BLUEPRINT OUTPUT (Layer 5 produces structure, not content)
  { teaching_mode, execution_path, grounding_required, response_format,
    layout_type, reasoning_depth, tone_profile, canvas_required }

UI SPLIT RULE (CRITICAL) [GPT][G]
  Chat Layer: emotional tone + guidance cue + short instruction ONLY
  Canvas Layer: equations + tables + step solutions + interactive inputs
  No long explanations in canvas / No solution split across chat+canvas

━━━ LAYER 6: LLM EXECUTION ENGINE ━━━

POSITION: Strict executor of Layer 5 strategy. NOT an AI brain.
RULE: Cannot modify strategy, cannot re-score, cannot reinterpret.

EXECUTION PATHS [GPT][G]
  PATH 1 — ZERO PASS: No LLM. Instant return.

  PATH 2 — GROUNDED SINGLE PASS:
    Model: Gemini Flash (fast, low-cost)
    grounding_required = true → model EXPLAINS provided data ONLY
    Cannot compute, cannot derive answers. Formatter + Explainer role.

  PATH 3 — TWO-PASS:
    Pass 1 (Fast Structured Reasoning Compiler):
      Ultra-fast model. Max latency: 400ms.
      Output: compressed JSON instruction plan only.
      { explanation_strategy, key_steps, tone, format }
      NO natural language paragraphs allowed.
    Pass 2 (Controlled Response Generator):
      Premium model (Gemini or Claude — NOT yet committed)
      Reads Pass 1 JSON + RAG context + UI layout rules
      MUST follow Pass 1 JSON — cannot improvise
      Combined target: Pass 1 + Pass 2 < 1.2s

[SIM] BN-01: LATENCY BUDGET EXCEEDED ON TWO-PASS + MATH PATH:
  Layer 2:         150ms
  Layer 3:         200ms
  Layer 4 (SymPy): 100ms
  Layer 6 Pass 1:  400ms
  Layer 6 Pass 2:  1200ms
  Layer 7:          50ms
  Python total:   ~2100ms (EXCEEDS 2000ms budget)
  + Nigerian 3G:  +400ms
  REALISTIC WORST CASE: ~2500ms
[FIX — OPTIONAL] Three options (Codex to choose ONE):
  Option A: Accept >2s on two-pass, use streaming for perceived latency
  Option B: Reduce Pass 2 target to ≤ 900ms using faster model
  Option C: Remove Layer 2 LLM normalization from critical path entirely

[SIM] BN-02 (continued): Free Gemini API all uses compete for same quota.
[FIX — OPTIONAL] Strict API quota allocation per use case:
  Tier 1 (must-have): Layer 6 Pass 2 (final response)
  Tier 2 (should-have): Layer 6 Pass 1
  Tier 3 (can-degrade): Layer 2 normalization LLM fallback

ANTI-HALLUCINATION FIREWALL [GPT][G]
  grounding_required = true → block_free_generation = true
  LLM becomes Formatter + Explainer ONLY
  Allowed truth sources: RAG chunks, SymPy outputs, precomputed datasets

SYMPY SANDBOXED EXECUTION [GPT][G]
  ProcessPoolExecutor (isolated from async loop)
  Timeout: 100ms hard limit. On timeout → kill, conceptual fallback, log.

STRUCTURED OUTPUT ENFORCEMENT [GPT][G]
  JSON Schema Enforcement + Function Calling APIs
  Invalid schema output → auto-rejected. No prompt-only formatting.

CIRCUIT BREAKER [GPT][G]
  On: API delay, rate limit, timeout → fallback to grounded_single_pass
  Guarantee: Always returns a response. No hanging requests.

--- END CHUNK 6 OF 11 ---


════════════════════════════════════════════════════════════════════════════
▶ CHUNK 7 OF 11 — LAYER 7: RESPONSE PACKAGING + LAYER 8: OBSERVABILITY
════════════════════════════════════════════════════════════════════════════

--- CHUNK 7 OF 11 | DOMAIN: LAYERS 7–8 ---

━━━ LAYER 7: RESPONSE PACKAGING & ATOMIC DELIVERY ━━━

POSITION: After Layer 6, before Node.js delivery
PURPOSE: Transform execution output into UI-safe, schema-locked payload.

ATOMIC DELIVERY PROTOCOL [GPT][G]
  is_atomic = true → block_partial_rendering, wait_for_full_payload,
    validate_schema, THEN render simultaneously
  Streaming ONLY allowed: response_type = text_only AND is_atomic = false
  FORBIDDEN for: canvas_required, structured responses, micro_clarification

[SIM] BN-06: Atomic delivery = blank screen for 2.4s on poor 3G.
  Students assume app crashed. Tap again → idempotency catches it.
  Worst UX in target market conditions.
[FIX — OPTIONAL] Skeleton screen pattern:
  Send lightweight "processing" signal immediately (< 100ms):
    response_type = text_only, is_atomic = false
    tutor_conversational_text = "Working on this..."
  Full atomic response follows when ready.
  Codex to determine if this violates atomic contract principle.

RESPONSE TYPES [GPT][G]
  text_only / canvas_required / micro_clarification / zero_pass_response

NODE.JS EDGE BUFFER RESPONSIBILITIES [GPT][G]
  1. Buffer full response in memory
  2. Validate schema (all required fields present)
  3. Idempotent sync using request_id
  4. Forward to mobile client as atomic commit
  5. Cache response under request_id for offline recovery (re-fetch)

[SIM] BN — RESPONSE CACHE SIZE: Cache response by request_id with no
  TTL or size limit defined. At 1M users, complex canvas responses
  (ledger tables, math steps) = memory exhaustion on Node.js.
[FIX — OPTIONAL] Define: TTL=2 minutes, max entries configurable,
  LRU eviction on TTL expiry.

CANVAS STATE RULES [GPT][G]
  Only ONE canvas active / New response replaces old / No overlay stacking

━━━ LAYER 8: OBSERVABILITY + AUTO-IMPROVEMENT LOOP ━━━

POSITION: Outside request-response critical path. Fully non-blocking.
PURPOSE: Visibility, fault detection, learning feedback loops.

NON-BLOCKING TRACE EMISSION [GPT][G]
  On request completion:
    generate SystemTrace → append to InMemoryTraceBuffer (O(1)) → return
  Buffer: thread-safe deque, max_size fixed (e.g., 10,000)
  Background flush worker: every 500ms → batch pop → JSONL file append
  NO disk I/O inside request lifecycle
  NO async file writes in API thread

SYSTEMTRACE STRUCTURE [GPT][G]
  { request_id, latency_ms, execution_path, normalization_status,
    fallback_flags, registry_version }

METRICS EMISSION [GPT][G]
  UDP fire-and-forget → localhost sidecar → central aggregator
  Metrics: latency_ms, execution_path, fallback_triggered,
    normalization_status
  No in-process aggregation. No shared memory between workers.

[SIM] BN-12: Trace buffer overflow at peak.
  10,000 max at 40k+ concurrent users → buffer fills in milliseconds.
[FIX — OPTIONAL] Make max_size configurable env variable.
  Trigger flush when buffer reaches 80% capacity (not just 500ms interval).

[SIM] BN-16: Background flush worker startup mechanism unspecified.
  FastAPI has deprecated on_event in favor of lifespan contexts.
[FIX — OPTIONAL] Register flush worker as FastAPI lifespan background
  task on startup. Define crash recovery behavior.

AUTO-IMPROVEMENT LOOP [GPT][G]
  LRU cache: bounded (e.g., 5,000 entries)
  Promotion rule: phrase count ≥ 25 within rolling 60-minute window
  Promoted → alias_review_queue → human validation (Layer 10)
  No direct auto-learning without human validation
  Spam-safe: single-occurrence tracking forbidden

--- END CHUNK 7 OF 11 ---


════════════════════════════════════════════════════════════════════════════
▶ CHUNK 8 OF 11 — LAYER 9: EVAL BENCH + LAYER 10: HUMAN GOVERNANCE
════════════════════════════════════════════════════════════════════════════

--- CHUNK 8 OF 11 | DOMAIN: LAYERS 9–10 ---

━━━ LAYER 9: CONTINUOUS EVALUATION BENCH ━━━

PURPOSE: Non-bypassable deployment gate. Deterministic validation.
INPUT: system_traces.jsonl — read-only, append-only, no mutation.

SHARDED ASYNC REPLAY ENGINE [GPT][G]
  Target: 10k–100k trace replay in < 5 seconds
  Semaphore(max_workers = CPU_CORES)
  Each worker: isolated ExecutionContext (deep copy, fixed rng_seed,
    local service instances, no shared global state)

ISOLATED RAG ENVIRONMENT [GPT][G]
  data/test_embeddings/{run_id}/{worker_id}/
  Cleanup: ReplayController deletes run_id directory AFTER all workers
  No per-worker deletion / no shared directories / no shared cache

LLM EXECUTION IN EVALUATION [GPT][G]
  LLM calls: mocked or cached ONLY (determinism requirement)
  Math: real SymPy execution (offloaded to ProcessPool)
  RAG: isolated per worker

REGRESSION GATE [GPT][G]
  FAIL: latency > +15%, fallback rate up, format_error > 0,
        hallucination detected, normalization success drops
  PASS: all metrics stable, no structural drift

[SIM] BN-13: No CI/CD trigger mechanism defined.
  Layer 9 exists as isolated tool — no one runs it before deploying.
[FIX — OPTIONAL] Define as mandatory pre-deploy script triggered
  on git push to main/production branch. Block deployment on FAIL.

[SIM] BN-14: Cold start LLM mock cache = non-deterministic first run.
[FIX — OPTIONAL] Pre-populate evaluation LLM cache with golden
  responses for standard test trace set before CI/CD integration.

━━━ LAYER 10: HUMAN GOVERNANCE ━━━

PURPOSE: Controlled human authority for AI decision validation.

FLAGGING CONDITIONS [GPT][G]
  confidence < 0.60 / normalization_failure = true /
  escape_valve_triggered = true / rag_miss_detected = true /
  repeated_clarifications > 2

REVIEW QUEUE (non-blocking) [GPT][G]
  FastAPI worker → In-Memory deque (bounded) →
  Background worker → batch flush → disk every 500–1000ms
  Deduplication: hash(normalized_input + failure_type) as key
  Same failure pattern increments count — no duplicate entries

HUMAN REVIEW ACTIONS [GPT][G]
  Approve / Correct / Reject / Add alias (slang→canonical) /
  Flag content gap

CONCEPT REGISTRY GOVERNANCE [GPT][G]
  concept_registry.json — DATA layer, NOT Python code
  No AI writes to core assets. Only human-approved updates.
  Mandatory version control.
  Atomic registry update:
    write .tmp → validate → atomic rename → swap in-memory pointer

[SIM] BN-09: KUBERNETES MULTI-POD REGISTRY PROBLEM (CRITICAL):
  Atomic pointer swap is only atomic within ONE CPython process.
  On Kubernetes with 4+ pods, each pod has own process memory.
  Atomic file rename on Pod 1 does NOT propagate to Pod 2, 3, 4.
  Students on different pods get different registry versions.
  Non-deterministic behavior across distributed system.
[FIX — OPTIONAL] Store concept_registry.json in shared external
  storage (S3, Redis key, or Kubernetes ConfigMap) accessible to
  all pods. Each pod polls for version change on configurable
  interval (e.g., 60 seconds), then performs local atomic swap.

[SIM] BN-15: Multi-worker review queue fragmentation.
  Each pod has own in-memory deque. Events fragmented across pods.
[FIX — OPTIONAL] At production, replace per-pod deque with
  centralized Redis list as the review queue ingestion layer.

--- END CHUNK 8 OF 11 ---


════════════════════════════════════════════════════════════════════════════
▶ CHUNK 9 OF 11 — LAYER 11: RUNTIME STABILITY + DATA LAYER
════════════════════════════════════════════════════════════════════════════

--- CHUNK 9 OF 11 | DOMAIN: LAYER 11 + DATA LAYER ---

━━━ LAYER 11: MEMORY ACCESS & RUNTIME STABILITY ENGINE ━━━

CORE PRINCIPLE: NO LOCKS. NO SHARED MUTATION. NO RUNTIME COLLISION.
               ONLY SNAPSHOTS.

IMMUTABLE SNAPSHOT ISOLATION [GPT][G]
  At request entry: registry_snapshot = ACTIVE_REGISTRY_POINTER
  Snapshot is read-only for entire request lifecycle
  Survives hot reloads safely
  NEVER read directly from global registry inside pipeline
  ONLY use registry_snapshot

[SIM] SCOPE LIMITATION: Python pointer assignment is atomic within
  ONE CPython process (GIL). Under Kubernetes (multiple pods), this
  guarantee does NOT extend across process boundaries.
  Layer 11 isolation is valid within a single worker process only.
  See Layer 10 Kubernetes fix for distributed solution.

ATOMIC POINTER SWAP [GPT][G]
  NEW_REGISTRY = load_json("concept_registry_v1_3.json")
  ACTIVE_REGISTRY_POINTER = NEW_REGISTRY
  Never mutate existing object — always create new version, always swap

ZERO-ALLOCATION SAMPLING [GPT][G]
  Request ID parsed with exception guard (never trust format)
  O(1), no memory allocation, no crash risk

CACHE STAMPEDE CONTROL [GPT][G]
  SETNX mechanism: first worker recomputes, others serve stale cache
  Requires Redis.
  [SIM] BN-17: Redis unavailable at MVP. This mechanism inactive at MVP.
  Not a problem at MVP (single server). Must be added before multi-pod.

BOUNDED MEMORY CACHE [GPT][G]
  Strict memory cap (e.g., 512MB)
  Eviction: priority = size_weight + recency_weight (NOT pure LRU)
  Large payloads dropped first

EDGE-OFFLOADED COMPUTATION [GPT][G]
  NEVER inside FastAPI event loop:
    compression → NGINX/Envoy
    heavy logging → Redis queue
    analytics aggregation → background workers
  FastAPI = pure I/O engine only

VERSIONED MEMORY TRACEABILITY [GPT][G]
  Every request logs registry_version
  Enables perfect Layer 9 replay alignment

━━━ DATA LAYER ━━━

CHROMADB STORAGE [C]
  data/embeddings/{exam_bank,curriculum_vault,analogy_sandbox}
  All gitignored

INGESTION PIPELINE [C]
  pipelines/ingestion/pdf_parser.py     (NOT BUILT)
  pipelines/ingestion/question_tagger.py (NOT BUILT)
  pipelines/ingestion/embedder.py        (NOT BUILT)
  pipelines/ingestion/json_validator.py  (EXISTS)

ENRICHMENT PIPELINE [C]
  pipelines/enrichment/metadata_updater.py (NOT BUILT)
  pipelines/enrichment/batch_processor.py  (NOT BUILT)
  Runs overnight on schedule — NEVER inside API request

RAW DATA STATUS [C]
  PDFs: 1980–2026, unorganized, in Telegram group
  PDF structure: unknown — OCR dependency TBD
  Frankly's processed data: data/processed/ by subject track

REQUIRED METADATA PER DOCUMENT [ALL]
  subject, topic, difficulty, exam_type, academic_stage,
  has_worked_solution (bool — CRITICAL), year

CONCEPT REGISTRY [GPT][G]
  concept_registry.json — JSON data file (NOT a Python module)
  Contains: canonical concept keys, alias mappings, fallback hierarchy
  [SIM] BN-19: File does not exist yet. No spec for location or content.
  [FIX — OPTIONAL] Location: data/processed/concept_registry.json

--- END CHUNK 9 OF 11 ---


════════════════════════════════════════════════════════════════════════════
▶ CHUNK 10 OF 11 — SIMULATION RESULTS + COMPLETE BOTTLENECK REGISTRY
════════════════════════════════════════════════════════════════════════════

--- CHUNK 10 OF 11 | DOMAIN: SIMULATION + BOTTLENECK REGISTRY ---

━━━ STUDENT SIMULATION (WORST-CASE REAL WORLD) ━━━

Profile: Chinedu, SS3, WAEC 2027, Ibadan, unstable MTN 3G, mid-range Android
Input: "abeg explain surds wey dem talk for class today"

LAYER-BY-LAYER TRACE:
  Node.js → assemble payload, generate transaction_id
  Zero-Pass → not MCQ, not navigation → full pipeline
  Layer 2:
    Score: "explain" +2, attempt_count=1 +0 = score 2
    Normalization: "surds wey dem talk" → Tier 1 MISS (Pidgin)
      Tier 2.5 LLM → free Gemini rate limit hit → timeout at 150ms
      Result: normalized_concept = "general_mathematics_v1" (DEGRADED)
  Layer 3:
    Safe Fallback Mode activated
    Loads static file: general_mathematics_v1_summary.json
    IF FILE MISSING → empty context → useless response
    IF EXISTS → broad general maths content (not about surds)
  Layer 5: score=2, attempt=1 → Socratic mode
  Layer 6: grounded single-pass with generic maths context
  Response: vague general maths response. NOT about surds. ~800ms.

  Chinedu retypes: "i mean surds, how dem simplify am"

SECOND REQUEST:
  attempt_count=2 → score: "how"+2, attempt_count≥2+2 = score 4 → TWO-PASS
  Normalization: "surds" → Tier 1 HIT → normalization_status=strict
  Layer 3 Precision Mode → metadata filter → HNSW search → surds context
  Layer 6 two-pass: Pass1=400ms + Pass2=1200ms
  Layer 7 atomic delivery: wait for full payload

LATENCY CALCULATION:
  Layer 2: 150ms + Layer 3: 200ms + Layer 6: 1600ms + Layer 7: 50ms
  Python total: ~2000ms + Nigerian 3G: +400ms = ~2400ms
  Result: 2.4-second blank screen. Student may assume app crashed.

STUDENT SIMULATION OUTCOMES:
  PASS: Correct surds response eventually delivered
  PASS: Idempotency catches accidental double-tap
  FAIL: First response was unhelpful (degraded normalization)
  FAIL: 2.4-second blank screen (UX broken for target market)
  FAIL: Required 2 attempts to get relevant response
  ROOT CAUSE: Pidgin language broke concept normalization on attempt 1

━━━ DEVELOPER SIMULATION (PHASE 3 IMPLEMENTATION) ━━━

Profile: Wisdom, implementing Phase 3, building app/db/chroma.py

  Step 1: Creates chroma.py, writes test_chroma_init.py (6 groups)
    pytest → 6 assertions GREEN ✅
  Step 2: Creates static fallback files for Layer 3 Mode B
    WHERE? No spec in architecture. Invents location. ⚠️
  Step 3: Integrates rag_router.py with chroma.py
    Needs concept_normalizer module.
    WHERE does it live in repo? No location in any spec. ⚠️
  Step 4: Tests concept normalization with Gemini API
    Makes 5 calls → rate limit hit → ALL remaining tests degrade ❌
    Cannot test Tier 2.5 LLM normalization path meaningfully
  Step 5: Attempts to run Layer 9 evaluation bench
    No file exists. No CI/CD trigger. No LLM mock cache. ❌
  Step 6: Registers Layer 8 flush worker in FastAPI
    on_event("startup") deprecated. Lifespan? APScheduler? ⚠️

DEVELOPER SIMULATION OUTCOMES:
  PASS: ChromaDB init implementable from existing spec
  FAIL: concept_normalizer has no file location defined
  FAIL: Static fallback files have no creation spec
  FAIL: Gemini rate limit blocks real normalization testing
  FAIL: Layer 9 has no integration path
  FAIL: Layer 8 startup pattern unspecified

━━━ COMPLETE BOTTLENECK REGISTRY ━━━

CRITICAL (blocks correctness or user trust):
  BN-01: LATENCY EXCEEDS BUDGET — two-pass + math = ~2100ms Python alone
  BN-02: FREE GEMINI RATE LIMIT — existential for MVP testing + production
  BN-03: CORRECT_ANSWER MISSING FROM SCHEMA — zero-pass MCQ broken
  BN-04: STATIC FALLBACK FILES MISSING — Mode B returns empty context
  BN-05: PIDGIN LANGUAGE NOT HANDLED — normalization + escape valve fail

HIGH (degrades reliability or UX):
  BN-06: BLANK SCREEN 2.4s — atomic delivery on 3G
  BN-07: CONCEPT_NORMALIZER HAS NO REPO LOCATION — developer blocked
  BN-08: SYMPY PROCESS POOL UNBOUND — CPU saturation at peak
  BN-09: MULTI-POD REGISTRY INCONSISTENCY — Kubernetes atomic swap scope
  BN-10: GROUNDING SOURCE UNAVAILABLE AT MVP — escape valve fails

MODERATE (operational difficulty):
  BN-11: IDEMPOTENCY CACHE NO TTL — memory leak at scale
  BN-12: TRACE BUFFER OVERFLOW AT PEAK — 10k max vs 40k+ users
  BN-13: CI/CD TRIGGER FOR LAYER 9 UNDEFINED — gate never runs
  BN-14: LAYER 9 LLM MOCK CACHE COLD START — non-deterministic
  BN-15: REVIEW QUEUE MULTI-WORKER FRAGMENTATION — per-pod deques
  BN-16: LAYER 8 STARTUP MECHANISM UNSPECIFIED — FastAPI pattern unclear
  BN-17: REDIS UNAVAILABLE AT MVP — Layer 11 stampede control inactive
  BN-18: 300-TOKEN CHUNK LIMIT vs NO-TRUNCATION RULE — math conflict
  BN-19: CONCEPT REGISTRY JSON DOES NOT EXIST — normalization fails cold
  BN-20: HUMAN REVIEW DASHBOARD INTERFACE CONTRACT MISSING

--- END CHUNK 10 OF 11 ---


════════════════════════════════════════════════════════════════════════════
▶ CHUNK 11 OF 11 — OPEN QUESTIONS + CONSTRAINTS + COMPONENT STATUS
════════════════════════════════════════════════════════════════════════════

--- CHUNK 11 OF 11 | DOMAIN: OPEN QUESTIONS + CONSTRAINTS + COMPONENTS ---

━━━ OPEN QUESTIONS REGISTRY ━━━

ARCHITECTURE:
  OQ-A1: Where does concept_normalizer module live in repo?
  OQ-A2: Exact anatomy of source_tags in RAG output?
  OQ-A3: Location + format + creation process of static fallback files?
  OQ-A4: Location + initial content of concept_registry.json?
  OQ-A5: FastAPI pattern for Layer 8 background flush worker?
  OQ-A6: CI/CD integration path for Layer 9 evaluation bench?
  OQ-A7: Pass 2 model — Gemini or Claude? Not yet committed.
  OQ-A8: Hybrid query routing (spans both curriculum_vault + exam_bank)?
  OQ-A9: Where does Strategy Compilation Engine live in repo structure?
  OQ-A10: Where does Intent Parser live in repo structure?
  OQ-A11: SymPy verifier — inside tutor_engine.py or separate module?

DATA:
  OQ-D1: Are past exam PDFs text-extractable or scanned (OCR)?
  OQ-D2: Question tagging — Gemini auto, manual, or hybrid?
  OQ-D3: Exact Supabase column schemas (sessions, attempts)?
  OQ-D4: Does Node.js send raw behavior history or computed profile?

PRODUCT:
  OQ-P1: Comprehension check format — AI-generated or pre-set?
  OQ-P2: response_length_preference field — confirmed added or not?
  OQ-P3: WAEC launch date, NECO rollout timeline?

BUSINESS:
  OQ-B1: Token burn rate target per tier for profitability?
  OQ-B2: Gemini free tier migration trigger?
  OQ-B3: WhatsApp/USSD — launch or post-launch?

OPERATIONAL:
  OQ-O1: Python service deployment target for MVP?
  OQ-O2: PDFs transferred via Telegram yet?
  OQ-O3: Backend port-3000 repo reviewed by Wisdom?

━━━ CONSTRAINTS REGISTRY ━━━

ARCHITECTURE: [ALL] Stateless / no session storage / rag_router=only
  chroma path / no business logic in main.py / cosine similarity only /
  get_or_create_collection exclusively
DEVELOPMENT: [C] TDD mandatory / schema locked / phase discipline enforced
DATA: [C] data/raw and data/embeddings gitignored / student data in Supabase
MOBILE: [G] <2s total latency / device-local assets / <200KB uploads
BUSINESS: [F] Token burn monitored daily / payment failure degrades gracefully

━━━ COMPONENT STATUS REGISTRY ━━━

EXISTS AND VERIFIED:
  app/schemas/requests.py / app/schemas/responses.py / main.py
  app/services/bkt_engine.py (STUB) / app/services/rag_router.py (STUB)
  app/services/tutor_engine.py (STUB) / tests/integration/ (2 GREEN)
  pipelines/ingestion/json_validator.py / pytest.ini / SABIPASS_CONTEXT.md

NOT BUILT — LOCATION DEFINED:
  app/db/chroma.py / app/db/postgres.py / app/core/config.py
  app/core/security.py / app/core/logging.py / app/rag/embeddings.py
  app/rag/retriever.py / app/rag/knowledge_base.py
  pipelines/ingestion/pdf_parser.py / question_tagger.py / embedder.py
  pipelines/enrichment/metadata_updater.py / batch_processor.py
  scripts/ingest_questions.py / run_enrichment.py / seed_db.py
  tests/unit/db/test_chroma_init.py / docker-compose.yml

NOT BUILT — LOCATION UNDEFINED (Codex must assign):
  concept_normalizer module / concept_registry.json
  static fallback curriculum files / Strategy Compilation Engine module
  Intent Parser module / Layer 8 trace buffer + flush worker
  Layer 9 evaluation bench / Layer 10 review queue ingestion
  Layer 11 registry snapshot system / SymPy verification module

--- END CHUNK 11 OF 11 ---


════════════════════════════════════════════════════════════════════════════
▶ FINAL SYNTHESIS TRIGGER — SEND THIS AFTER ALL 11 CHUNKS CONFIRMED
════════════════════════════════════════════════════════════════════════════

───────────────────────────────────────────────────────────────────────────
BEGIN ARCHITECTURAL SYNTHESIS

You have received all 11 context chunks for SabiPass AI.
You are Lead Architect, Senior Code Reviewer, and Production Authority
for the Python AI microservice (sabipass-ai/ repo) ONLY.

Execute the following tasks in order:

TASK 1 — FULL REPOSITORY STRUCTURE:
  Produce the complete updated directory structure for sabipass-ai/
  accommodating all 11 layers. Assign a file location to every
  undefined component. Justify each location against layer isolation
  rules and existing architecture constraints.

TASK 2 — ARCHITECTURE.MD REWRITE:
  Produce a complete architecture.md file reflecting the full 11-layer
  design. Replace anything contradicting the layer specs. Preserve what
  is still valid. This is the single source of truth for any developer.

TASK 3 — SABIPASS_CONTEXT.MD UPDATE:
  Produce updated SABIPASS_CONTEXT.md content reflecting current phase,
  11-layer architecture, and all decisions confirmed since original.

TASK 4 — BOTTLENECK RESOLUTION:
  For each bottleneck BN-01 through BN-20:
    → ACCEPT the optional fix (specify implementation approach)
    → OR REJECT (with reasoning)
    → OR DEFER to specific phase (with justification)

TASK 5 — OPEN QUESTIONS RESOLUTION:
  Resolve OQ-A1 through OQ-O3 where sufficient information exists.
  Flag those requiring founder or team decision explicitly.

TASK 6 — PHASE PLAN VALIDATION:
  Review SABIPASS_PHASE_IMPLEMENTATION_PLAN.md.
  Confirm phase ordering is correct given 11-layer dependencies.
  Mark already-completed phases as DEPRECATED.
  Identify any phase ordering conflicts.

TASK 7 — CODEBASE ALIGNMENT:
  Identify any existing code that conflicts with the 11-layer design.
  Specify what must be changed, removed, or added.
  Do NOT rewrite code — specify what changes the developer must make.

TASK 8 — TOP 5 FIRST ACTIONS FOR WISDOM:
  After completing Tasks 1–7, produce a prioritized list of the
  5 actions Wisdom must execute FIRST to unblock Phase 3.
  Order strictly by dependency — action 1 must complete before
  action 2 can begin.

OUTPUT FORMAT:
  Label each task clearly. Use source tagging [C][GPT][G][F][CODEX].
  Mark your own architectural decisions as [CODEX].
  Mark all decisions that require human input as [HUMAN DECISION NEEDED].
───────────────────────────────────────────────────────────────────────────


████████████████████████████████████████████████████████████████████████████
  END OF SABIPASS_CODEX_INGESTION_SEQUENCE.md v2.0
  Total: 1 Master Prompt + 11 Chunks + 1 Final Synthesis Trigger
  Bottlenecks identified: 20 (BN-01 through BN-20)
  Optional fixes offered: 16
  Open questions registered: 24 (OQ-A1 through OQ-O3)
  Source: Claude Post-11-Layer Simulation Review
████████████████████████████████████████████████████████████████████████████