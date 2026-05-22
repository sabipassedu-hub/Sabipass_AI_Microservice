import json
from pathlib import Path

import pytest

from app.schemas.requests import NeuralChatRequest
from app.services.learning_state_adapter import (
    LearningStateValidationError,
    validate_and_normalize_learning_state,
)
from tests.unit.services.test_tutor_engine import build_request


REPO_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = REPO_ROOT / "data" / "processed" / "concept_registry.json"


def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def test_state_machine_rejects_unknown_micro_skill():
    request = build_request()
    request.learning_session_state = request.learning_session_state.model_copy(
        update={"micro_skill": "invented_micro_skill"}
    )

    with pytest.raises(LearningStateValidationError, match="micro_skill"):
        validate_and_normalize_learning_state(request, registry_snapshot=load_registry())


def test_state_machine_rejects_evaluation_attempt_zero_at_schema_boundary():
    payload = build_request().model_dump()
    payload["learning_session_state"]["phase"] = "evaluation"
    payload["learning_session_state"]["attempt"] = 0

    with pytest.raises(ValueError, match="evaluation phase"):
        NeuralChatRequest.model_validate(payload)


def test_state_machine_normalizes_practice_attempt_jump():
    request = build_request()
    request.learning_session_state = request.learning_session_state.model_copy(
        update={
            "phase": "practice",
            "attempt": 9,
            "last_question_ids": ["q1", "q2"],
            "correct_pattern": [True, False],
        }
    )

    result = validate_and_normalize_learning_state(
        request,
        registry_snapshot=load_registry(),
    )

    assert result.state.attempt == 3
    assert result.status == "normalized"
    assert "attempt_jump_normalized" in result.issues


def test_state_machine_keeps_llm_out_of_progression_metadata():
    request = build_request()
    request.learning_session_state = request.learning_session_state.model_copy(
        update={
            "phase": "practice",
            "attempt": 3,
            "streak": 2,
            "last_question_ids": ["q1", "q2", "q3"],
            "correct_pattern": [True, True],
        }
    )

    result = validate_and_normalize_learning_state(
        request,
        registry_snapshot=load_registry(),
    )

    assert result.next_phase == "evaluation"
    assert result.metadata()["llm_controls_progression"] is False


def test_state_machine_applies_anti_guessing_weight():
    request = build_request()
    request.learning_session_state = request.learning_session_state.model_copy(
        update={
            "phase": "evaluation",
            "attempt": 1,
            "last_question_ids": ["q1", "q2", "q3"],
            "correct_pattern": [True, False, True],
            "response_time_ms": 900,
            "confidence_level": "low",
        }
    )

    result = validate_and_normalize_learning_state(
        request,
        registry_snapshot=load_registry(),
    )

    assert result.anti_guessing_signal == "guessing_risk_low_confidence_fast_inconsistent"
    assert result.mastery_weight_multiplier == 0.5


def test_state_machine_accepts_node_topic_id_alias_and_topic_node_alignment():
    payload = build_request().model_dump()
    payload["current_interaction_context"]["topic_node"] = "linear_equations"
    payload["learning_session_state"] = {
        "topic_id": "linear_equations",
        "subtopic": "solving_basic_equations",
        "micro_skill": "solving_basic_equations",
        "session_phase": "explanation",
        "attempt_number": 0,
        "current_streak": 0,
        "mastery": 0.0,
        "state_version": 1,
        "current_question_id": None,
        "last_question_ids": [],
        "correct_pattern": [],
        "response_time_ms": None,
        "confidence_level": None,
        "hints_used": 0,
        "difficulty": "easy",
        "is_retention_check": False,
    }
    request = NeuralChatRequest.model_validate(payload)

    result = validate_and_normalize_learning_state(
        request,
        registry_snapshot=load_registry(),
    )

    assert result.state.topic == "linear_equations"
    assert result.state.subtopic == "solving_basic_equations"
    assert result.next_phase == "guided_example"
