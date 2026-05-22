from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_readme_documents_local_demo_commands():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert "python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000" in readme
    assert "streamlit run streamlit_test/app.py" in readme
    assert "scripts\\seed_db.py" in readme
    assert "SABI_AI_API_URL" in readme
    assert "SABI_DEMO_MODE=true" in readme


def test_pytest_uses_workspace_basetemp_for_chroma():
    pytest_ini = (REPO_ROOT / "pytest.ini").read_text(encoding="utf-8")

    assert "--basetemp=.pytest_tmp" in pytest_ini
    assert "cache_dir = .pytest_tmp/cache" in pytest_ini


def test_requirements_include_streamlit_for_demo():
    requirements = (REPO_ROOT / "requirements.txt").read_text(encoding="utf-8")

    assert "streamlit" in requirements
