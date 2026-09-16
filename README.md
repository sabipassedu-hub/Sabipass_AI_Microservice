# SabiPass AI Microservice

> Python-based AI cognition service for personalized tutoring, curriculum support, homework explanation, and WAEC/JAMB exam preparation.

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

## Overview

SabiPass AI Microservice is the cognition layer of the SabiPass learning platform. It transforms a student's current question and learning context into a structured tutoring response that can be rendered by the SabiPass web or mobile application.

The service combines:

- Personalized tutoring decisions based on learning and mastery signals.
- Retrieval-augmented generation (RAG) for curriculum-aware responses.
- English and Nigerian Pidgin intent and concept handling.
- WAEC and JAMB mathematics content support.
- Tier-aware model routing for free, premium, and efficiency modes.
- Deterministic zero-pass handling for supported multiple-choice submissions.
- Math processing and verification using SymPy and related tooling.
- Structured canvas directives for step-by-step solutions, interactive quizzes, and split-view learning content.
- Health checks, request admission controls, bounded retries, circuit protection, and OpenTelemetry instrumentation.

## Service Boundary

This service owns tutoring cognition only. The Node.js product backend remains the system of record and owns:

- Authentication and authorization.
- Subscription and billing state.
- Student preferences and persisted history.
- Idempotency and request deduplication.
- Teach First and product-policy gates.
- Supabase access and application persistence.

All communication with this service is server-to-server. Browser and mobile clients must not call the Python service directly.

## Architecture

The request pipeline is designed around the following stages:

1. Node.js assembles authorized student and learning context.
2. FastAPI validates and admits the request.
3. The strategy layer identifies intent, complexity, and normalized concepts.
4. The RAG layer retrieves relevant curriculum material or uses a controlled fallback summary.
5. The tutoring layer selects an appropriate response strategy.
6. LiteLLM routes the request to the configured model.
7. The response is validated and packaged into the SabiPass response contract.
8. Observability data is emitted for operational monitoring.

The service is provider-agnostic at the application layer through LiteLLM. Model selection is controlled through environment variables rather than direct provider SDK integrations.

## API

### Health and readiness

```text
GET /health
GET /ready
GET /api/v1/health
GET /api/v1/ready
```

### Neural tutoring endpoint

```text
POST /api/v1/neural/chat
```

The endpoint accepts a canonical request containing request metadata, student identity, execution mode, learning signals, emotional telemetry, current interaction context, and historical mastery data.

Example request:

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
  "current_interaction_context": {
    "raw_whiteboard_input": "How I go solve 2x + 4 = 10?",
    "topic_node": "linear_equations",
    "history_tokens": [],
    "errors_on_same_concept_space": 0,
    "previous_bot_response_id": null
  },
  "historical_mastery_map": {
    "active_weakness_arrays": ["linear_equations"],
    "passed_topics_arrays": []
  }
}
```

The response contract supports `text_only`, `canvas_required`, `micro_clarification`, and `zero_pass_response` response types. See [`NODE_JS_CONTRACT.md`](NODE_JS_CONTRACT.md) for the complete request/response contract, field definitions, error handling, tier rules, and security requirements.

## Technology Stack

- Python 3.11+
- FastAPI and Uvicorn
- Pydantic and pydantic-settings
- ChromaDB and FastEmbed for retrieval
- LiteLLM for provider-agnostic model routing
- SymPy and math-verify for mathematical processing
- pyBKT-compatible learning signals
- Streamlit demonstration interface
- OpenTelemetry instrumentation
- Pytest and pytest-asyncio
- Docker and Docker Compose

## Getting Started

### Prerequisites

- Python 3.11 or newer.
- Docker and Docker Compose for containerized execution.
- An LLM provider key for live model execution. The demo can also run in deterministic demo mode.

### Local installation

Create and activate a virtual environment, then install dependencies:

```bash
python -m venv .venv

# macOS/Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Create a local environment file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Set the provider key and, if required, model configuration in `.env`:

```dotenv
GROQ_API_KEY=your_groq_key_here
TIER_FREE_MODEL=groq/llama-3.1-8b-instant
TIER_PREMIUM_MODEL=groq/llama-3.3-70b-versatile
EFFICIENCY_MODE_MODEL=groq/llama-3.1-8b-instant
SABI_DEMO_MODE=true
```

### Run the API

```bash
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at `http://127.0.0.1:8000`. Interactive API documentation is available at `/docs` when enabled by the FastAPI application.

For local demo data, the service bootstraps Chroma from `data/raw/mock/` when `SABI_BOOTSTRAP_MOCK_DATA=true` or when the setting is not provided. To prewarm the embedding model and local collections:

```bash
python scripts/seed_db.py
```

### Run the Streamlit demonstration

Start the API first, then run:

```bash
python -m streamlit run streamlit_test/app.py
```

To use a different API URL:

```bash
export SABI_AI_API_URL="http://127.0.0.1:8000/api/v1/neural/chat"
```

The demonstration supports curriculum, homework explainer, and WAEC/JAMB exam preparation flows using stable mock curriculum data.

## Docker Deployment

Build and run the service directly:

```bash
docker build -t sabipass-ai .
docker run --env-file .env -p 8000:8000 sabipass-ai
```

Or use Docker Compose:

```bash
docker compose up --build
```

The container exposes port `8000` and includes a health check against `/health`. For production deployments, disable mock bootstrapping and manage embeddings and curriculum data separately:

```dotenv
SABI_DEMO_MODE=false
SABI_BOOTSTRAP_MOCK_DATA=false
```

The current deployment target is a correctly tuned single-server MVP. Kubernetes, Redis, multi-pod registry coordination, and direct Python-to-Supabase integration are intentionally outside the current MVP boundary.

## Testing

Run the complete test suite:

```bash
python -m pytest
```

For Windows-safe execution with temporary pytest files outside the repository:

```powershell
python -m pytest -o cache_dir=$env:TEMP\sabipass_pytest_cache --basetemp=$env:TEMP\sabipass_pytest_tmp
```

The documented implementation verification includes coverage for API contracts, schema validation, English and Pidgin routing, strategy compilation, model routing, retrieval and fallback behavior, mock ingestion, and end-to-end tutoring flows.

## Repository Structure

```text
.
├── app/                    # FastAPI application, schemas, strategies, RAG, and services
├── data/                   # Raw mock inputs and processed curriculum artifacts
├── docs/                   # Architecture and engineering documentation
├── evaluation/             # Evaluation and quality-assessment resources
├── pipelines/              # Data ingestion and processing pipelines
├── scripts/                # Operational and database-seeding scripts
├── streamlit_test/         # Demonstration application
├── tests/                  # Unit, integration, and contract tests
├── main.py                 # FastAPI application entry point
├── Dockerfile              # Production container definition
├── docker-compose.yml      # Local/container orchestration
├── NODE_JS_CONTRACT.md     # Node.js integration contract
├── README.md               # Project documentation
├── .env.example            # Environment configuration template
└── .gitignore              # Git ignore rules
```

## Integration and Security Notes

- Node.js must send the student's current subscription tier on every request.
- Python enforces configured history limits for free, premium, and efficiency modes.
- `correct_answer` is accepted only for server-side exam multiple-choice submissions and must never be exposed to clients.
- Internal system metadata, provider details, credentials, and private learning signals must not be displayed directly to students.
- Node.js owns idempotency; Python does not deduplicate transaction IDs.
- Validation failures (`422`) indicate an integration payload problem and should not be retried without correction.
- Temporary upstream or service failures (`500`/`503`) may be handled by the Node.js caller with controlled retry and fallback behavior.

## Project Status

The core demo pipeline is implemented, including contract validation, strategy compilation, concept normalization, provider-agnostic routing, RAG precision and fallback behavior, mock ingestion, and end-to-end demo flows. The project is currently focused on strengthening production readiness, including evaluation gates, security hardening, trace delivery, and expanded governance.

## Documentation

- [`NODE_JS_CONTRACT.md`](NODE_JS_CONTRACT.md) — integration contract for the Node.js backend.
- [`SABIPASS_CONTEXT.md`](SABIPASS_CONTEXT.md) — service scope, architecture decisions, and delivery context.
- [`docs/`](docs/) — architecture and engineering documentation.

## License and Commercial Use

This repository contains proprietary SabiPass product technology. Licensing, deployment, and commercial-use terms should be agreed with the SabiPass project owners before redistribution or production use.
