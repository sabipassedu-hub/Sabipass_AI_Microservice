import json
from pathlib import Path

from app.services.strategy.concept_normalizer import NormalizationResult, normalize_concept


REPO_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = REPO_ROOT / "data" / "processed" / "concept_registry.json"


def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def test_normalize_exact_canonical_key_as_strict_match():
    result = normalize_concept("linear_equations", registry_snapshot=load_registry())

    assert result == NormalizationResult(
        concept_key="linear_equations",
        confidence=1.0,
        status="strict",
        matched_text="linear_equations",
    )


def test_normalize_pidgin_alias_inside_student_phrase():
    result = normalize_concept(
        "Abeg how i go find x for this equation?",
        registry_snapshot=load_registry(),
    )

    assert result.concept_key == "linear_equations"
    assert result.status == "strict"
    assert result.confidence == 0.95
    assert result.matched_text == "how i go find x"


def test_normalize_misspelled_alias_to_canonical_topic():
    result = normalize_concept("This qudratic equation hard me.", registry_snapshot=load_registry())

    assert result.concept_key == "quadratic_equations"
    assert result.status == "strict"
    assert result.matched_text == "qudratic equation"


def test_normalize_plain_x_squared_phrase_to_quadratic_topic():
    result = normalize_concept(
        "solve x squared plus 5x plus 6",
        registry_snapshot=load_registry(),
    )

    assert result.concept_key == "quadratic_equations"
    assert result.status == "strict"
    assert result.matched_text == "x squared"


def test_normalize_display_name_by_local_semantic_match():
    result = normalize_concept(
        "Please help with trig ratios in a right triangle.",
        registry_snapshot=load_registry(),
    )

    assert result.concept_key == "trigonometric_ratios"
    assert result.status == "semantic"
    assert result.confidence == 0.9


def test_normalize_degrades_unknown_math_prompt_to_general_parent():
    result = normalize_concept(
        "I need help with this mathematics question from class.",
        registry_snapshot=load_registry(),
    )

    assert result == NormalizationResult(
        concept_key="general_mathematics",
        confidence=0.4,
        status="degraded",
        matched_text=None,
    )


def test_normalize_returns_micro_clarification_status_when_not_math():
    result = normalize_concept("Open my profile settings.", registry_snapshot=load_registry())

    assert result.concept_key is None
    assert result.confidence == 0.0
    assert result.status == "needs_clarification"
    assert result.matched_text is None
