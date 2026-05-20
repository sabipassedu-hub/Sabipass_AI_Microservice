from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PLAN_PATH = REPO_ROOT / "SABIPASS_PHASE_IMPLEMENTATION_PLAN.md"
LOG_PATH = REPO_ROOT / "SESSIONS_LOG.md"
LATEST_NOTES_LIMIT = 600


def _latest_session_notes(plan_text: str) -> str:
    marker = "## Latest Session Notes"
    return plan_text.split(marker, maxsplit=1)[1].strip()


def test_plan_declares_session_notes_size_policy():
    plan = PLAN_PATH.read_text(encoding="utf-8")

    assert "Keep `SABIPASS_PHASE_IMPLEMENTATION_PLAN.md` at or below 300 lines." in plan
    assert "Keep `Latest Session Notes` at or below 600 characters." in plan
    assert "Move previous session notes into `SESSIONS_LOG.md`" in plan


def test_plan_stays_fast_to_read():
    plan_lines = PLAN_PATH.read_text(encoding="utf-8").splitlines()

    assert len(plan_lines) <= 300


def test_latest_session_notes_stay_short():
    plan = PLAN_PATH.read_text(encoding="utf-8")

    assert len(_latest_session_notes(plan)) <= LATEST_NOTES_LIMIT


def test_sessions_log_archives_previous_notes():
    log = LOG_PATH.read_text(encoding="utf-8")

    assert "## 2026-05-19 - MVP Context Alignment" in log
    assert "Verified full test suite: 28 passed." in log
