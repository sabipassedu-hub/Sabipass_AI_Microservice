# SabiPass AI Microservice

Python cognition service for SabiPass tutoring flows.

## Local Demo

Install dependencies from the repository root:

```powershell
..\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Copy the environment template before setting provider keys:

```powershell
Copy-Item .env.example .env
```

Create or update `.env` with your provider key. Model env vars are optional
because the local demo defaults to Groq model IDs that work through LiteLLM:

```powershell
GROQ_API_KEY=your_groq_key_here
TIER_FREE_MODEL=groq/llama-3.1-8b-instant
TIER_PREMIUM_MODEL=groq/llama-3.3-70b-versatile
EFFICIENCY_MODE_MODEL=groq/llama-3.1-8b-instant
SABI_DEMO_MODE=true
```

Start the FastAPI service:

```powershell
..\venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

If your virtual environment is already activated:

```powershell
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Health checks are available at `GET /health` and `GET /ready`. Versioned aliases
are also available at `GET /api/v1/health` and `GET /api/v1/ready`.

On startup the service seeds local demo Chroma data from `data/raw/mock/` when
`SABI_BOOTSTRAP_MOCK_DATA=true` or unset. Set it to `false` for a production
deployment with separately managed embeddings.

Before a VC demo, prewarm the local embedding model and Chroma collections so
the first live question does not pay the FastEmbed download or database setup
cost:

```powershell
..\venv\Scripts\python.exe scripts\seed_db.py
```

In a second terminal, start the Streamlit demo:

```powershell
..\venv\Scripts\python.exe -m streamlit run streamlit_test/app.py
```

The VC demo should run with `SABI_DEMO_MODE=true`. Supported demo prompts use
deterministic SabiPass tutoring responses, while unsupported prompts can still
use the bounded live model path when provider credentials are available. The
Streamlit view pins student chat requests to the Freemium tier, displays Gemini
as the active student-facing model, and shows Claude 4.6 Opus as a locked
Premium upsell. It includes curriculum, homework explainer, and WAEC/JAMB exam
prep modes using stable mock curriculum data until the full curriculum dataset
lands.

The demo calls `POST /api/v1/neural/chat` with the same canonical payload shape that Node.js sends. To point the demo at another service URL:

```powershell
$env:SABI_AI_API_URL="http://127.0.0.1:8000/api/v1/neural/chat"
..\venv\Scripts\python.exe -m streamlit run streamlit_test/app.py
```

For operator-only payload inspection in Streamlit, set
`SABI_STREAMLIT_SHOW_OPERATOR_JSON=true`. Leave it unset for student-facing or
investor walkthroughs so provider details and internal metadata stay hidden.

Run tests from the repository root. For Windows-safe verification that keeps
pytest cache and temp data outside the repo, use:

```powershell
..\venv\Scripts\python.exe -m pytest -o cache_dir=$env:TEMP\sabipass_pytest_cache --basetemp=$env:TEMP\sabipass_pytest_tmp
```

`pytest.ini` also keeps Chroma's temporary SQLite files inside `.pytest_tmp/`
for the default local command:

```powershell
..\venv\Scripts\python.exe -m pytest
```

## Deployment

Build and run the production container:

```powershell
docker build -t sabipass-ai .
docker run --env-file .env -p 8000:8000 sabipass-ai
```

The container starts with:

```powershell
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Keep `data/raw/mock/waec_mathematics_mock_parse.json` in the checkout when
`SABI_BOOTSTRAP_MOCK_DATA=true`; readiness checks use it to verify demo seed
data is available before traffic is sent to the service.
