from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_context_uses_mvp_scale_target_from_master_directive():
    context = (REPO_ROOT / "SABIPASS_CONTEXT.md").read_text(encoding="utf-8")

    assert "100,000 users" in context
    assert "Not concurrent" in context
    assert "single-server" in context
    assert "1M+" not in context


def test_context_uses_current_eleven_layer_pipeline():
    context = (REPO_ROOT / "SABIPASS_CONTEXT.md").read_text(encoding="utf-8")

    assert "11. Registry snapshot stability." in context
    assert "12." not in context
