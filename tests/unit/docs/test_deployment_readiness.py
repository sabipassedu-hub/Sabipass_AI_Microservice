from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_env_example_documents_runtime_settings():
    env_example = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")

    assert "GROQ_API_KEY=" in env_example
    assert "SABI_BOOTSTRAP_MOCK_DATA=true" in env_example
    assert "REQUEST_ADMISSION_MAX_CONCURRENT=24" in env_example
    assert "OBSERVABILITY_TRACE_LOG_PATH=logs/sabipass_traces.jsonl" in env_example


def test_dockerfile_uses_production_uvicorn_command():
    dockerfile = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "FROM python:3.12-slim" in dockerfile
    assert 'CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]' in dockerfile


def test_readme_documents_phase7_deployment_and_windows_pytest():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert (
        r"..\venv\Scripts\python.exe -m pytest -o cache_dir=$env:TEMP\sabipass_pytest_cache --basetemp=$env:TEMP\sabipass_pytest_tmp"
        in readme
    )
    assert "GET /health" in readme
    assert "docker build -t sabipass-ai ." in readme
    assert "data/raw/mock/waec_mathematics_mock_parse.json" in readme


def test_demo_seed_file_is_packaged_for_clean_checkout():
    seed_path = REPO_ROOT / "data" / "raw" / "mock" / "waec_mathematics_mock_parse.json"
    gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")

    assert seed_path.exists()
    assert "!data/raw/mock/waec_mathematics_mock_parse.json" in gitignore
