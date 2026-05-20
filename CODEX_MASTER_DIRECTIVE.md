# SabiPass AI - Codex Master Directive

This document is the single source of director-level decisions for the
SabiPass AI Python microservice. It lives in the repository as permanent
reference. Every Codex session must read this file alongside
docs/ARCHITECTURE.md and ENGINEERING_GUIDELINES.md before doing anything.

This document does not tell you how to implement things. The architecture
and engineering guidelines do that. This document tells you what has been
decided, what the target is, what is in scope, and what is not.

---

## What This Service Is

A Python AI cognition microservice. It is not a chat app. It is not the
Node.js product backend. It receives structured requests from Node.js,
runs a tutoring pipeline, and returns structured responses. Node.js owns
everything outside cognition. Python owns cognition only.

The primary user is a Nigerian secondary school student preparing for
WAEC or JAMB examinations. The system must understand Pidgin English as
a first-class input language, not as an edge case.

---

## Resolved Decisions

### LLM Provider

The system is provider-agnostic via LiteLLM. No LLM provider is
hard-coded anywhere. The model used is controlled entirely by environment
variables. Swapping from Claude to Gemini to Groq to Ollama requires
only changing an env var and restarting. The code must never import an
LLM SDK directly - all LLM calls go through LiteLLM only.

Add litellm to requirements.txt. Design the model router and LLM
executor stubs around this from the start.

### Tier and Token System

There are two user tiers and one user-controlled efficiency toggle.

Free tier: limited interactions per session, smaller model, one turn
of history maximum, single-pass execution path only.

Premium tier: full interactions, best available model, three turns of
history, two-pass execution path allowed.

Efficiency mode: a toggle available to both tiers. When on, it
downgrades the execution path by one level, drops history to zero turns,
and uses a cheaper model. Users trade intelligence for speed and cost.
This is a setting the student controls, not something the system decides.

These must be env-configurable per tier:
  TIER_FREE_MODEL
  TIER_PREMIUM_MODEL
  TIER_FREE_MAX_HISTORY_TURNS
  TIER_PREMIUM_MAX_HISTORY_TURNS
  EFFICIENCY_MODE_MODEL

### Scale Target

100,000 users. Not concurrent. A correctly tuned single-server
deployment handles this. Build for correctness and clean architecture,
not for Kubernetes-level distribution. Kubernetes is not in scope for
any current phase.

### Deployment Target

MVP deployment is Railway or Render, Docker container, deployed from
GitHub on push. This is zero-cost for early stage. The Python service
and Node.js service deploy independently. They communicate only through
the API contract defined in NODE_JS_CONTRACT.md.

No Kubernetes. No multi-pod registry. No Redis for MVP. These are
production-scale concerns for a later phase after the product has users.

### PDF Ingestion Pipeline

The data analyst has not yet delivered source PDFs. Do not wait for
them. Create a mock ingestion pipeline that reads from
data/raw/mock/ - plain JSON files shaped exactly like what a real PDF
parser would produce. The pipeline must be written so that replacing
the mock loader with a real PDF parser requires changing one file only,
not restructuring the pipeline.

### Concept Registry

Populate data/processed/concept_registry.json with real WAEC and JAMB
mathematics canonical topics, Pidgin aliases, common shortforms, and
misspellings that Nigerian secondary school students actually use.
Include a fallback hierarchy mapping narrow topics to broad parents.
Also write real foundational content into the general mathematics
fallback summary file. Both files were created as empty shells and need
real content before Layer 2 can function.

### Node.js Contract File

Create a file at the root of the repository called NODE_JS_CONTRACT.md.

This file is for the Node.js team, who have not yet written their
backend. It must document, in plain language with full schema examples:

- The exact request shape Python expects at POST /api/v1/neural/chat
- The exact response shape Python returns
- What Node.js must compute and send (student state, tier, history,
  BKT signals, emotional telemetry)
- What Python will never fetch itself (Supabase state, auth tokens,
  user preferences, subscription status)
- How idempotency works: Node.js caches duplicate uuid_transaction_id
  responses with a TTL - Python does not handle this
- Error codes and what they mean for the Node.js consumer
- How the tier and efficiency mode flags are passed
- How the zero-pass correct_answer field works and when it is allowed
- Security: requests are server-to-server, this field must never reach
  client-side

This file must be complete enough that the Node.js team can build their
side independently without needing to ask questions.

### Demo Frontend

Create a Streamlit test interface in a folder called streamlit_test/ at
the repository root. It must call the FastAPI endpoint exactly as
Node.js would. It is for demonstration and development testing only,
not for production. It must show a realistic tutoring interaction: a
student input field, response display, a tier selector, and an
efficiency mode toggle. This is what will be shown to investors.

---

## Demo Target

The system is working when this end-to-end flow succeeds:

A student types a question - in English or Pidgin - about a WAEC
mathematics topic. The system recognises the concept, retrieves relevant
context if available, and returns a pedagogically appropriate response
through the configured LLM. The response respects the student's tier
and efficiency mode setting.

This must be demonstrable through the Streamlit interface with a real
LLM API key in the environment.

---

## What Is In Scope Now

- Populating the concept registry and fallback summaries with real content
- Implementing Layer 2 fully: complexity scorer, intent parser, concept
  normalizer, StateStrategy compiler
- Integrating LiteLLM and implementing the model router
- Implementing the RAG router precision and fallback modes
- Wiring the full pipeline in neural_chat.py
- Creating NODE_JS_CONTRACT.md
- Creating the Streamlit demo frontend
- Creating the mock PDF ingestion pipeline
- Writing the SABIPASS_PHASE_IMPLEMENTATION_PLAN.md as a living
  checklist that every session updates

---

## What Is Out Of Scope Until After Demo

Do not build these now. Do not design around them now. Do not reference
them in implementation unless the architecture already requires a stub.

- Kubernetes, multi-pod registry, Redis
- Full evaluation bench and regression gate
- Human governance review queue beyond the stub
- Production security hardening
- Full observability and trace flushing beyond the stub
- WhatsApp and USSD integration
- Supabase direct integration from Python

---

## Implementation Rules For Every Session

Read docs/ARCHITECTURE.md, ENGINEERING_GUIDELINES.md, and this file
before writing a single line of code.

Work in small increments. One logical unit per session. Tests before
marking anything done. The original 18 tests must pass after every
session. Never implement an item whose dependencies above it are
incomplete.

After each session, update SABIPASS_PHASE_IMPLEMENTATION_PLAN.md with
accurate status markers. That file is the live checklist. If it is not
updated, the session is not finished.

No over-engineering. If something works simply, ship the simple version.
The goal is a working, demonstrable, investable product. Not a
perfectly distributed system.

---

## How To Create The Implementation Plan

On the first session after reading this file, create
SABIPASS_PHASE_IMPLEMENTATION_PLAN.md following the rules and structure
already specified in the prompt history. That file is your working
checklist for every session after it exists. This directive is the why
and the what. The plan is the how and the when.
