import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = REPO_ROOT / "data" / "processed" / "concept_registry.json"
FALLBACK_PATH = (
    REPO_ROOT
    / "data"
    / "processed"
    / "fallback"
    / "general_mathematics_v1_summary.json"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_concept_registry_has_required_shape():
    registry = load_json(REGISTRY_PATH)

    assert set(registry) == {"version", "canonical_keys", "aliases", "fallback_hierarchy"}
    assert isinstance(registry["version"], str)
    assert isinstance(registry["canonical_keys"], dict)
    assert isinstance(registry["aliases"], dict)
    assert isinstance(registry["fallback_hierarchy"], dict)
    assert registry["canonical_keys"]


def test_canonical_registry_entries_have_valid_links():
    registry = load_json(REGISTRY_PATH)
    canonical_keys = registry["canonical_keys"]
    required_topic_fields = {
        "display_name",
        "subject",
        "strand",
        "parent_key",
        "exam_coverage",
        "academic_stages",
        "description",
    }

    for key, topic in canonical_keys.items():
        assert key == key.lower()
        assert set(topic) == required_topic_fields
        assert topic["display_name"]
        assert topic["subject"] == "mathematics"
        assert topic["strand"]
        assert topic["parent_key"] is None or topic["parent_key"] in canonical_keys
        assert isinstance(topic["exam_coverage"], list)
        assert set(topic["exam_coverage"]) <= {"WAEC", "JAMB"}
        assert topic["exam_coverage"]
        assert isinstance(topic["academic_stages"], list)
        assert topic["academic_stages"]
        assert topic["description"]


def test_registry_aliases_and_fallback_hierarchy_target_canonical_keys():
    registry = load_json(REGISTRY_PATH)
    canonical_keys = set(registry["canonical_keys"])

    for alias, canonical_key in registry["aliases"].items():
        assert alias == alias.strip().lower()
        assert canonical_key in canonical_keys

    for child_key, parent_key in registry["fallback_hierarchy"].items():
        assert child_key in canonical_keys
        assert parent_key in canonical_keys
        assert child_key != parent_key


def test_general_mathematics_fallback_summary_has_required_shape():
    summary = load_json(FALLBACK_PATH)

    assert set(summary) == {"concept_key", "summary_text", "token_count", "version"}
    assert summary["concept_key"] == "general_mathematics_v1"
    assert isinstance(summary["version"], str)
    assert isinstance(summary["summary_text"], str)
    assert summary["summary_text"].strip()
    assert isinstance(summary["token_count"], int)
    assert 0 < summary["token_count"] <= 600


def test_general_mathematics_fallback_summary_is_foundational():
    summary = load_json(FALLBACK_PATH)
    text = summary["summary_text"]
    normalized = text.lower()

    assert summary["token_count"] == len(text.split())
    assert "waec" in normalized
    assert "jamb" in normalized
    assert "algebra" in normalized
    assert "geometry" in normalized
    assert "trigonometry" in normalized
    assert "probability" in normalized
    assert "statistics" in normalized
