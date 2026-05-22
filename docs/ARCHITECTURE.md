# SabiPass AI Microservice Architecture

SabiPass AI is the Python cognition service for a structured Nigerian exam tutoring platform. It is not a chat backend and not the Node.js product backend.

## Scope

Python owns tutoring cognition only: zero-pass evaluation, strategy compilation, RAG execution, deterministic math processing, tutor decisioning, controlled LLM execution, response packaging, observability traces, evaluation replay, governance queue ingestion, and registry snapshots.

Python must not own accounts, subscriptions, payments, persisted student sessions, Supabase student state, parent/school policy, moderation policy, or Teach First gate enforcement. Node.js sends already-authorized, already-gated requests.

## Curriculum-Controlled Learning Engine

SabiPass AI is a curriculum-controlled learning engine, not a passive tutoring chatbot. The system may adapt explanations, examples, and scaffolding, but it must never dynamically invent the curriculum path or let the LLM decide progression.

Curriculum authority:
- Topics, subtopics, and micro-skills are predefined from the approved NIRDC-aligned curriculum graph.
- The curriculum graph hierarchy is required: topic -> subtopic -> micro-skill.
- A topic contains ordered subtopics; each subtopic contains the smallest testable micro-skills.
- Registry aliases may map student language to approved keys, but no request may create a new topic, subtopic, or micro-skill.
- If an approved topic lacks enough grounded curriculum or exam-bank material, the engine must use controlled fallback summaries or mark the topic unavailable for chat teaching until content is repaired.

Structured topic-session flow:
- `explanation`: adaptive explanation grounded in curriculum context;
- `guided_example`: a worked example selected from curriculum or exam-bank material;
- `practice`: controlled practice loop with easy-to-medium-to-hard difficulty progression;
- `evaluation`: scored attempt with confidence, difficulty, hint usage, and variation signals;
- `mastery_decision`: system-calculated result that updates subtopic mastery and emits frontend unlock signals.

Progression ownership:
- Python may emit mastery, unlock eligibility, retention, and intervention recommendations.
- Node.js/frontend controls topic navigation, locks, unlocks, and session persistence.
- The chat response must not say that the student has moved to the next topic as an instruction of record. It may explain that the latest result makes the student eligible for the next frontend-controlled step.

## Mastery Logic

Mastery is tracked at subtopic level. Topic mastery is an aggregation of its subtopics and must not be inferred from a single correct answer.

Minimum decision rules:
- Unlock and mastery thresholds are configurable per subject and exam target, not global constants.
- Threshold config must provide `unlock_threshold` and `mastery_threshold`; WAEC/JAMB mathematics may use `0.70` and `0.80` respectively as configured values.
- `score >= unlock_threshold`: next topic becomes unlock-eligible outside chat.
- `score >= mastery_threshold`: topic can be marked mastered only if required subtopics are mastered.
- Topic mastery requires evidence across the difficulty ladder, not only easy questions.
- Failure on a retained/revisited mastered topic reduces the relevant subtopic mastery and can move the topic back to weak status.
- Micro-skill weakness must be logged when repeated errors cluster on the same micro-skill.

Anti-guessing is mandatory. Each evaluated answer must enforce at least one of:
- correct streak requirement, such as 2-3 correct answers in a row for the same subtopic;
- question variation enforcement, so repeated attempts cannot reuse the same item shape;
- student confidence input, such as low, medium, high, or numeric equivalent;
- hint penalty, so heavily hinted correct answers contribute less to mastery.

Confidence is part of the learning signal. Student-facing confidence input is `low | medium | high`; Python maps it through a configured numeric scale in the `0.0-1.0` range before mastery and pyBKT-compatible updates:
- high-confidence correct answers raise mastery more than low-confidence correct answers;
- high-confidence wrong answers are strong misconception signals;
- low-confidence correct answers require another varied item before mastery is considered stable;
- missing confidence should be treated as unknown, not as high confidence.

## Failure Handling Model

The failure ladder is system-controlled and based on attempts against the current subtopic or micro-skill:
- Attempt 1: normal retry with concise corrective feedback.
- Attempt 2: simplified explanation and easier variant.
- Attempt 3: deeper breakdown at micro-skill level.
- Attempt 4: system intervention.

Attempt 4 intervention must identify the weakest observed sub-skill and present structured recovery options:
- relearn foundation;
- guided walkthrough mode;
- simplified examples.

The engine must not ask open-ended questions like "what don't you understand" as the intervention path. It may ask a bounded choice question only when the options are system-generated recovery modes.

## Retention Model

Mastery is not permanent. The learning engine must support spaced reinforcement:
- previously mastered topics reappear later as short retention checks;
- retention checks select from weak or decayed subtopics before fully mastered ones;
- failed retention reduces subtopic mastery and may reclassify the topic as weak;
- Python computes the retention schedule and emits the due topic/subtopic/micro-skill, due time, and decay reason;
- Node.js persists the schedule and triggers the future retention check through the frontend/session flow.

## Open-Source Fit

Use mature libraries where they reduce risk without taking over product rules:
- pyBKT is suitable for subtopic and micro-skill mastery probability updates once attempt-level records include skill id, correctness, confidence, difficulty, hint use, and item id.
- py-fsrs or an equivalent FSRS implementation is suitable for retention scheduling, but SabiPass must still own curriculum unlock and remediation rules.
- catsim or other IRT/CAT tooling is useful for offline evaluation of difficulty ladders and item selection quality; do not put CAT in charge of curriculum progression.
- NetworkX is useful for validating and traversing the predefined topic/subtopic/micro-skill graph. It must read approved registry data rather than generating curriculum.

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
- `app_execution_mode`: `exam_prep | curriculum_coach | homework_explainer | general_prompt | navigation_click`
- `cognitive_aptitude_profile`: regression/velocity, scaffolding, tolerance, decay fields
- `emotional_telemetry`: rage/caps/frustration/sentiment/focus fields
- `current_interaction_context`: `raw_whiteboard_input`, `topic_node`, last 3 history tokens, `errors_on_same_concept_space`
- `historical_mastery_map`: active weaknesses and passed topics
- `learning_session_state`: persisted frontend-owned topic session snapshot, including `topic_id`, `subtopic_id`, `micro_skill_id`, `session_phase`, `attempt_number`, `difficulty_level`, `current_streak`, `last_question_signature`, `hint_count`, `student_confidence`, and retention flags

For zero-pass MCQ only, `current_interaction_context.correct_answer` is allowed when `app_execution_mode = exam_prep` and the selected input is `A-D`. It must be server-to-server only.

`learning_session_state` must contain only approved curriculum keys from the registry snapshot. Python validates and reasons over this state, but Node.js remains the source of truth for persistence, restore, frontend topic navigation, and unlock visibility. Every resumed request must restore phase, attempt number, difficulty level, and active micro-skill.

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

Learning-engine response additions:
- `neural_sync_payload.mastery_updates`: subtopic and micro-skill mastery deltas, confidence-adjusted BKT inputs, topic aggregation, weak-skill markers, and retention due dates;
- `neural_sync_payload.progression_recommendation`: `locked | unlock_eligible | mastered | weak_reinforcement_due | intervention_required`;
- `system_metadata.learning_engine`: session phase, teaching mode, failure stage, difficulty level, anti-guessing rule applied, RAG grounding status, and whether progression was frontend-controlled.

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
- learning state snapshot: approved topic, subtopic, micro-skill, session phase, attempt number, difficulty level, streak, confidence, hint count, retention state, and weak-skill candidates;
- RAG strategy;
- pedagogy strategy;
- model strategy.

Downstream layers may execute strategy, not mutate it.

Layer 2 must reject, degrade, or clarify when the request refers to a topic not present in the registry snapshot. It may select a fallback parent key only from the approved fallback hierarchy.

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

Learning-engine RAG constraints:
- teaching content must be grounded in `curriculum_vault`, `exam_bank`, or approved fallback summaries;
- WAEC/JAMB practice and evaluation items must prefer `exam_bank` records with difficulty and worked-solution metadata;
- if retrieval is weak for the requested topic/subtopic, the engine must either use controlled summaries for foundational teaching or return topic-unavailable metadata for frontend repair/retry handling;
- RAG misses must not cause dynamic topic generation.

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
- Guided Example
- Practice
- Evaluation
- System Intervention
- Retention Check

Direct Answer requires verified grounding from exam bank, structured solution JSON, or SymPy. If unavailable, return a trust-preserving guided approach, not a hallucinated answer.

Layer 5 owns the mastery rules. It must select the teaching mode from session phase, subtopic mastery, difficulty level, attempt number, streak, confidence, hint count, and RAG grounding status.

Failure ladder:
- attempt 1 uses normal retry;
- attempt 2 uses simplified explanation;
- attempt 3 breaks the task into micro-skills;
- attempt 4 emits system intervention with bounded recovery options.

Mastery decision:
- update subtopic mastery after evaluation;
- aggregate topic mastery from subtopics;
- apply anti-guessing before unlock or mastery recommendations;
- treat repeated weak answers as micro-skill evidence, not generic chat confusion.

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

The LLM must not:
- create topics, subtopics, or micro-skills;
- choose the next curriculum topic;
- mark mastery;
- unlock progression;
- override the failure ladder;
- ignore the difficulty level selected by the system.

Prompts must pass the system-selected teaching mode, session phase, difficulty level, grounding context, and recovery option set as constraints. The model may adapt wording, examples, and scaffolding inside those constraints.

## Layer 7: Packaging

`app/services/response_packager.py` validates and atomically packages full responses. Canvas/structured payloads remain atomic.

Python does not send two HTTP responses for one POST. Node/mobile may show a local processing skeleton while Python works. Streaming is allowed only for non-atomic `text_only`.

Learning-engine packaging must support structured teaching modes:
- explanation payloads identify target subtopic and micro-skill;
- guided examples include worked steps and difficulty;
- practice payloads include item id/signature, difficulty, variation marker, and hint policy;
- evaluation payloads include score, confidence, streak, hint penalty, and next required evidence;
- intervention payloads include weak micro-skill and bounded recovery options;
- retention payloads include due reason and decay effect.

The response may recommend progression state, but must mark frontend navigation as externally controlled.

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

Learning-engine evaluation scenarios must cover:
- subtopic mastery aggregation into topic mastery;
- 70 percent unlock eligibility and 80 percent mastered state;
- easy-to-medium-to-hard difficulty ladder;
- anti-guessing via streak, variation, confidence, or hint penalty;
- repeated failure attempts 1 through 4;
- attempt 4 structured intervention without open-ended confusion prompts;
- confidence-weighted BKT updates;
- retention decay and mastered-topic regression to weak status;
- weak RAG fallback and topic-unavailable handling.

## Layer 10: Human Governance

Human review events are non-blocking. MVP uses bounded file-backed queue; production uses Redis.

Review actions: approve, correct, reject, add alias, flag content gap. No AI writes directly to registry assets.

Layer 10 must log learning failure patterns for human review:
- unresolved topic/subtopic/micro-skill keys;
- repeated attempt-4 interventions;
- high-confidence wrong answers;
- repeated low-confidence correct answers;
- RAG misses for approved curriculum nodes;
- item signatures that permit guessing or repetition;
- retention failures on previously mastered topics.

## Layer 11: Registry Snapshot Stability

Requests read an immutable registry snapshot captured at entry. In-process pointer swap is valid only within one worker. Multi-pod production requires external shared registry storage plus polling and local atomic swaps.

## Data

Chroma collections:
- `exam_bank`
- `curriculum_vault`
- `analogy_sandbox`

Curriculum registry assets:
- canonical topics, subtopics, and micro-skills are registry data, not model output;
- the graph must explicitly define topic -> subtopic -> micro-skill hierarchy and reject orphaned nodes;
- each curriculum node must include `subject`, `topic_id`, required child ids at the appropriate level, `academic_stage`, `exam_coverage`, prerequisites, and allowed difficulty range;
- question records must include `item_id`, `subtopic_id`, `micro_skill_ids`, `difficulty`, `question_signature`, `answer_key`, `worked_solution_status`, and source metadata;
- recovery content must map weak micro-skills to approved foundation lessons, guided walkthroughs, and simplified examples.

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

Curriculum-controlled learning engine phase:
1. extend request/response schemas with learning session state, confidence, difficulty, streak, hint, and variation fields;
2. add an explicit curriculum graph registry for approved topic -> subtopic -> micro-skill hierarchy, prerequisites, and available content status;
3. replace the current heuristic BKT adapter with a confidence-aware mastery engine that reads per-subject/exam thresholds and emits pyBKT-compatible attempt records;
4. implement failure ladder, intervention selection, anti-guessing, Python-computed retention scheduling, and difficulty progression in rule-based services;
5. add evaluation gates for mastery, retention, repeated failure, anti-guessing, and weak RAG scenarios;
6. add governance logs for curriculum gaps and failure patterns.
