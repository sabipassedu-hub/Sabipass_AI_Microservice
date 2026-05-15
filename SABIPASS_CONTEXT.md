# SABIPASS AI CONTEXT ENGINE CONSTRAINTS
- Architecture: 100% Stateless FastAPI Microservice.
- State Sync: All updated BKT mastery metrics MUST be passed back via the JSON response envelope. Never write local session files.
- ChromaDB Constraint: Must use 3 strict, independent collection paths (`exam_bank`, `curriculum_vault`, `analogy_sandbox`). Mixed-collection vector scans are forbidden.
- TDD Constraint: Every feature file must have a matching validation file inside the `tests/` directory.
