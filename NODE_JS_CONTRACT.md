# SabiPass Node.js Integration Contract

This document is the server-to-server contract between the Node.js product
backend and the SabiPass AI Python cognition service.

Python owns tutoring cognition only. Node.js owns auth, subscriptions,
student state, persistence, idempotency, client preferences, and all Supabase
access.

## Endpoint

`POST /api/v1/neural/chat`

The request body must be JSON. Node.js should send the canonical field names
shown here. Python accepts a few legacy aliases during migration, but Node.js
should not build new code around those aliases.

## Request Shape

```json
{
  "request_metadata": {
    "uuid_transaction_id": "b1c61bd8-26d0-4b2d-9f56-7ff520ad0d4f",
    "timestamp": "2026-05-19T12:00:00Z",
    "device_latency_ms": 140
  },
  "student_identity": {
    "student_db_id": "student_tunde_01",
    "tier": "free",
    "academic_scope": "senior_secondary_2",
    "exam_target": "WAEC"
  },
  "efficiency_mode": false,
  "app_execution_mode": "exam_prep",
  "cognitive_aptitude_profile": {
    "regression_slope": 0.12,
    "scaffolding_flag": "medium",
    "complexity_tolerance": "medium",
    "knowledge_decay_params": "medium"
  },
  "emotional_telemetry": {
    "rage_clicks": [],
    "caps_lock_aggression": [],
    "detected_frustration_signals": ["repeated_wrong_answer"],
    "sentiment_trends": "stable",
    "latency_focus_integrity": 0.91
  },
  "current_interaction_context": {
    "raw_whiteboard_input": "How I go solve 2x + 4 = 10?",
    "topic_node": "linear_equations",
    "history_tokens": [
      "student: I no understand equations",
      "assistant: Let's isolate x step by step"
    ],
    "errors_on_same_concept_space": 1,
    "previous_bot_response_id": "resp_20260519_001"
  },
  "historical_mastery_map": {
    "active_weakness_arrays": ["linear_equations", "fractions"],
    "passed_topics_arrays": ["basic_arithmetic"]
  }
}
```

## Request Fields

`request_metadata`

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `uuid_transaction_id` | string | yes | Node.js-generated UUID for request tracking and idempotency. |
| `timestamp` | string | yes | ISO-8601 UTC timestamp from Node.js. |
| `device_latency_ms` | integer | yes | Client/device latency already measured by Node.js or mobile. |

`student_identity`

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `student_db_id` | string | yes | Supabase student ID or Node-owned student identifier. |
| `tier` | `"free"` or `"premium"` | yes | Subscription tier computed by Node.js. Python never checks billing. |
| `academic_scope` | string | yes | Example: `junior_secondary_3`, `senior_secondary_2`. |
| `exam_target` | string | yes | Example: `WAEC`, `JAMB`, `WAEC 2027`. |

`efficiency_mode`

Boolean user-controlled toggle. When `true`, Python drops history to zero
turns and downstream model routing must choose the cheaper efficiency model.
This is never inferred by Python; Node.js must send the user's current setting
on every request.

`app_execution_mode`

Allowed values:

- `exam_prep`
- `curriculum_coach`
- `general_prompt`
- `navigation_click`

`cognitive_aptitude_profile`

Node.js computes and sends these learning signals from product state:

| Field | Type | Notes |
| --- | --- | --- |
| `regression_slope` | number | Recent learning velocity or decline signal. |
| `scaffolding_flag` | string | Example: `low`, `medium`, `high`. |
| `complexity_tolerance` | string | Example: `low`, `medium`, `high`. |
| `knowledge_decay_params` | string | Retention/decay estimate from Node-owned state. |

`emotional_telemetry`

Node.js computes and sends these session signals:

| Field | Type | Notes |
| --- | --- | --- |
| `rage_clicks` | string array | Product-detected rage-click events. |
| `caps_lock_aggression` | string array | Product-detected aggressive caps usage. |
| `detected_frustration_signals` | string array | Examples: repeated erase, repeated wrong answer. |
| `sentiment_trends` | string | Example: `improving`, `stable`, `frustrated`. |
| `latency_focus_integrity` | number | Focus/latency integrity score. |

`current_interaction_context`

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `raw_whiteboard_input` | string | yes | The student's exact current input. Pidgin is first-class input. |
| `topic_node` | string | yes | Node's current topic hint, if known. Send `""` if unknown. |
| `history_tokens` | string array | yes | Recent conversation snippets. Python enforces tier limits. |
| `errors_on_same_concept_space` | integer | yes | Current repeated-error count for the concept space. |
| `previous_bot_response_id` | string or null | no | Node-owned response/session reference. |
| `correct_answer` | `"A"`, `"B"`, `"C"`, `"D"` or null | no | Server-only zero-pass MCQ answer key. See below. |

`historical_mastery_map`

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `active_weakness_arrays` | string array | yes | Node-owned active weakness/topic keys. |
| `passed_topics_arrays` | string array | yes | Node-owned mastered topic keys. |

## Tier And History Rules

Node.js must pass `student_identity.tier` on every request.

Python currently enforces these default history limits:

| Tier/mode | Default history accepted by Python |
| --- | --- |
| Free | Last 1 turn |
| Premium | Last 3 turns |
| Efficiency mode on | 0 turns |

The tier limits are environment-configurable in Python:

- `TIER_FREE_MAX_HISTORY_TURNS`
- `TIER_PREMIUM_MAX_HISTORY_TURNS`

Node.js may send more history than the tier allows, but Python will trim it.
For predictable cost and latency, Node.js should send only the allowed amount.

## Zero-Pass MCQ Rules

`current_interaction_context.correct_answer` is allowed only when all of these
are true:

- `app_execution_mode` is `exam_prep`;
- the student's `raw_whiteboard_input` is a selected option `A`, `B`, `C`, or `D`;
- the request is server-to-server from Node.js to Python.

Example:

```json
{
  "app_execution_mode": "exam_prep",
  "current_interaction_context": {
    "raw_whiteboard_input": "B",
    "topic_node": "quadratic_equations",
    "history_tokens": [],
    "errors_on_same_concept_space": 0,
    "correct_answer": "C"
  }
}
```

`correct_answer` must never be sent to the browser, mobile client, analytics
payloads visible to clients, or any client-side cache. It exists only so Python
can perform zero-pass correctness handling without RAG or LLM work.

## What Node.js Must Compute And Send

Node.js must send:

- authenticated student identity;
- subscription tier;
- current efficiency-mode setting;
- academic scope and exam target;
- bounded recent history;
- BKT/mastery-derived learning signals;
- emotional telemetry;
- active weaknesses and mastered topics;
- current topic hint, when known;
- zero-pass `correct_answer`, only for server-side exam MCQ submissions.

## What Python Will Never Fetch

Python will not fetch or compute:

- Supabase student records;
- auth tokens or session authorization;
- subscription status or payment state;
- user preferences;
- parent/school policy;
- Teach First gate status;
- persisted conversation history;
- Node.js idempotency cache entries.

If Python needs a signal for cognition, Node.js must include that signal in
the request.

## Idempotency

Node.js owns idempotency.

For duplicate `request_metadata.uuid_transaction_id` values, Node.js must
return the cached response for a short TTL instead of calling Python again.
Python does not deduplicate transactions, does not own the TTL, and does not
look up previous responses.

Recommended Node.js behavior:

1. Receive client request.
2. Generate or verify `uuid_transaction_id`.
3. Check Node-owned cache for that transaction ID.
4. If present, return cached Python response.
5. If absent, call Python, cache the response by transaction ID, and return it.

## Response Shape

Python returns `SabiNeuralResponse`.

```json
{
  "request_id": "b1c61bd8-26d0-4b2d-9f56-7ff520ad0d4f",
  "response_type": "canvas_required",
  "is_atomic": true,
  "tutor_conversational_text": "Good attempt. Let's isolate x by removing 4 from both sides first.",
  "canvas_directive": {
    "render_type": "step_by_step_solution",
    "canvas_meta": {
      "concept_key": "linear_equations"
    },
    "payload_data": [
      {
        "step": 1,
        "text": "2x + 4 = 10"
      },
      {
        "step": 2,
        "text": "2x = 6"
      },
      {
        "step": 3,
        "text": "x = 3"
      }
    ]
  },
  "micro_rewards": {
    "trigger_animation": null,
    "praise_type": "effort",
    "xp_boost_awarded": 0
  },
  "neural_sync_payload": {
    "updated_bkt_mastery": 0.53,
    "calculated_learning_velocity": 0.04,
    "updated_weakness_array": ["linear_equations"]
  },
  "system_metadata": {
    "pipeline_status": "ok",
    "model": "env-selected-model",
    "tier": "free",
    "efficiency_mode": false
  }
}
```

`response_type`

Allowed values:

- `text_only`
- `canvas_required`
- `micro_clarification`
- `zero_pass_response`

`canvas_directive`

May be `null`. When present, `render_type` must be one of:

- `step_by_step_solution`
- `interactive_quiz_game`
- `split_view_doc`

`micro_rewards`

May be `null`. When present, Node.js/mobile may use it for lightweight reward
effects. It must not be treated as source of truth for billing or progression.

`neural_sync_payload`

May be `null` in future response types, but current successful responses return
an object shaped as shown above. Node.js decides what to persist.

`system_metadata`

Diagnostic metadata for backend logs and debugging. Do not display raw
`system_metadata` directly to students.

## Error Codes

| HTTP status | Meaning for Node.js |
| --- | --- |
| `200` | Python accepted the request and returned a structured tutoring response. |
| `422` | Request failed schema validation. Node.js sent missing, malformed, or disallowed fields. Do not retry without changing the payload. |
| `500` | Unexpected Python service failure. Node.js may retry with backoff or return a controlled product error. |
| `503` | Python or an upstream cognition dependency is temporarily unavailable. Node.js may retry with backoff. |

Current FastAPI validation errors use the default `detail` array:

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "request_metadata"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

Node.js should log validation responses with the transaction ID and fix the
caller payload. Validation errors are integration bugs, not student-facing
tutoring failures.

## Security Boundary

All requests to Python are server-to-server. The browser and mobile client must
never call Python directly.

Never expose these fields client-side:

- `correct_answer`;
- internal mastery calculations not intended for the student;
- raw `system_metadata`;
- server auth credentials or service URLs.

Python trusts Node.js for authorization and gating. Node.js must not forward
unauthorized client payloads to Python.
