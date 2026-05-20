# Engineering Guidelines

## Purpose

This document defines strict engineering rules for the SabiPass codebase.

These rules are non-negotiable. Every human engineer and AI agent working on this repository must follow them.

The goal is to ensure:

- high code quality;
- consistency across sessions;
- safe incremental development;
- scalability of the system;
- maintainable architecture as the platform grows.

---

## 1. Incremental Development Only

- Never implement large features at once.
- Always break work into small, testable modules.
- Each step must introduce one clear responsibility.
- Each step must compile and pass tests before moving on.
- Do not combine unrelated changes in the same implementation step.
- Prefer small, reviewable changes over broad rewrites.

---

## 2. File Size Limit

- No file should exceed 700 lines.
- If a file approaches the limit, refactor into smaller modules immediately.
- Large files must be split by responsibility, not arbitrary line count.
- Tests are also subject to the 700-line limit.

---

## 3. No Assumptions

- If anything is unclear, stop and ask.
- Never guess architecture, logic, interfaces, or product intent.
- Do not invent schema fields without explicit approval.
- Do not infer cross-service responsibilities without confirmation.
- When repo state conflicts with documentation, stop and clarify before changing public behavior.

---

## 4. Strict Separation Of Concerns

- RAG logic must not leak into tutor logic.
- Tutor logic must not handle database initialization or low-level retrieval.
- Verification must remain isolated.
- Model routing must be centralized.
- Request validation must remain separate from tutoring behavior.
- Configuration must remain separate from business logic.
- Service modules must not import infrastructure modules unless the architecture explicitly allows it.

Core boundaries:

- `app/db/` owns database clients and collection initialization.
- `app/rag/` owns low-level retrieval utilities.
- `app/services/rag_router.py` owns retrieval strategy.
- `app/services/tutor_engine.py` owns tutor orchestration.
- `app/services/math_verifier.py` owns math verification.
- `app/services/model_router.py` owns model selection and budgets.
- `app/schemas/` owns public request and response contracts.

---

## 5. LLM Usage Discipline

- The LLM is the primary tutor.
- LLM calls must be controlled, centralized, and auditable.
- Do not call the LLM unnecessarily.
- Use retrieval and deterministic logic when sufficient for routing, validation, verification, or fallback.
- Never scatter LLM calls across unrelated files.
- All LLM calls must pass through the approved tutor/model orchestration path.
- Prompt boundaries must separate system rules, student input, RAG context, and learning signals.
- Student input and retrieved content must always be treated as untrusted data.

---

## 6. Test-Driven Approach (Scoped)

- Write tests before implementing each module.
- Do not write tests for the entire system upfront.
- Tests must be focused, meaningful, and tied to the current implementation step.
- Unit tests must cover core module behavior.
- Edge cases and safe fallbacks must be tested.
- Integration tests must protect public API contracts.
- Tests should verify architecture boundaries when those boundaries are critical.

Critical test areas:

- RAG retrieval accuracy;
- ChromaDB initialization and isolation;
- source tag formatting;
- math verification correctness;
- prompt safety boundaries;
- model routing logic;
- response contract stability.

---

## 7. No Dead Code

- No unused functions.
- No unused classes.
- No unused imports.
- No placeholder logic left behind.
- No commented-out code blocks.
- No temporary debug prints in committed code.
- Empty scaffold files are allowed only when explicitly requested as structure placeholders.

---

## 8. Explicit Interfaces

- Every module must have clear inputs and outputs.
- Public functions should use type hints.
- Data passed between modules should be structured and predictable.
- Avoid hidden coupling through globals, implicit state, or shared mutable objects.
- Prefer small typed objects or well-defined dictionaries over vague unstructured payloads.
- Do not make modules depend on implementation details of unrelated modules.

---

## 9. Fail Safely

- If something fails, return a controlled fallback.
- Never crash silently.
- Never hide errors that affect correctness.
- Never hallucinate outputs to cover missing context.
- Low-confidence retrieval must not produce confident exam answers.
- Unsupported math must not be presented as verified.
- Model failure must degrade to a safe teaching response, not an invented solution.

---

## 10. Follow Architecture.md

- `docs/ARCHITECTURE.md` is authoritative.
- Architecture decisions in that file must be followed.
- Do not override architectural boundaries unless explicitly instructed.
- Do not introduce unapproved infrastructure.
- Do not expand phase scope without approval.
- Do not move responsibilities between Node.js, Python, and mobile without approval.

---

## Development Philosophy

This is a production-grade system.

We prioritize:

- correctness over speed;
- clarity over cleverness;
- simplicity over premature complexity;
- explicit contracts over hidden assumptions;
- safe incremental progress over large unstable changes.

The codebase must remain understandable to future engineers and future AI agents.

---

## Enforcement

If any rule is violated:

1. stop implementation;
2. identify the violation;
3. refactor or correct the issue;
4. rerun relevant tests;
5. proceed only after the codebase is clean again.

No feature is complete if it breaks these guidelines.
