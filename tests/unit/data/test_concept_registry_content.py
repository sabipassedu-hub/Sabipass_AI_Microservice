import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = REPO_ROOT / "data" / "processed" / "concept_registry.json"


def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def test_registry_contains_core_waec_jamb_math_topics():
    registry = load_registry()
    canonical_keys = registry["canonical_keys"]

    required_keys = {
        "linear_equations",
        "quadratic_equations",
        "simultaneous_equations",
        "indices",
        "logarithms",
        "surds",
        "trigonometric_ratios",
        "circle_theorems",
        "coordinate_geometry",
        "probability",
        "statistics",
        "differentiation",
    }

    assert required_keys.issubset(canonical_keys)

    for key in required_keys:
        topic = canonical_keys[key]
        assert topic["subject"] == "mathematics"
        assert set(topic["exam_coverage"]) >= {"WAEC", "JAMB"}
        assert topic["display_name"]
        assert topic["strand"]
        assert topic["description"]


def test_registry_aliases_cover_pidgin_shortforms_and_misspellings():
    registry = load_registry()
    aliases = registry["aliases"]

    expected_aliases = {
        "how i go find x": "linear_equations",
        "make x stand alone": "linear_equations",
        "quad eqn": "quadratic_equations",
        "qudratic equation": "quadratic_equations",
        "x squared": "quadratic_equations",
        "simul eqn": "simultaneous_equations",
        "log": "logarithms",
        "surd": "surds",
        "trig ratio": "trigonometric_ratios",
        "cicle theorem": "circle_theorems",
        "probabilty": "probability",
    }

    for alias, canonical_key in expected_aliases.items():
        assert aliases[alias] == canonical_key


def test_all_alias_targets_are_canonical_keys():
    registry = load_registry()
    canonical_keys = set(registry["canonical_keys"])

    for alias, canonical_key in registry["aliases"].items():
        assert alias == alias.lower()
        assert canonical_key in canonical_keys
