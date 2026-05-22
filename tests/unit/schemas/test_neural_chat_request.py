import pytest
from pydantic import ValidationError

from app.schemas.requests import (
    MAX_HISTORY_TOKEN_LENGTH,
    MAX_HISTORY_TOKENS,
    MAX_MASTERY_ITEMS,
    MAX_RAW_WHITEBOARD_INPUT_LENGTH,
    MAX_TELEMETRY_EVENTS,
    NeuralChatRequest,
)


def valid_payload(
    *,
    tier: str = "free",
    efficiency_mode: bool = False,
    app_execution_mode: str = "general_prompt",
    raw_whiteboard_input: str = "Solve 2x + 4 = 10",
    history_tokens: list[str] | None = None,
    correct_answer: str | None = None,
) -> dict:
    interaction_context = {
        "raw_whiteboard_input": raw_whiteboard_input,
        "topic_node": "linear_equations",
        "history_tokens": history_tokens or [],
        "errors_on_same_concept_space": 0,
    }
    if correct_answer is not None:
        interaction_context["correct_answer"] = correct_answer

    return {
        "request_metadata": {
            "uuid_transaction_id": "txn-schema-test-001",
            "timestamp": "2026-05-19T12:00:00Z",
            "device_latency_ms": 120,
        },
        "student_identity": {
            "student_db_id": "student_schema_001",
            "tier": tier,
            "academic_scope": "senior_secondary_2",
            "exam_target": "WAEC",
        },
        "efficiency_mode": efficiency_mode,
        "app_execution_mode": app_execution_mode,
        "cognitive_aptitude_profile": {
            "regression_slope": 0.2,
            "scaffolding_flag": "medium",
            "complexity_tolerance": "medium",
            "knowledge_decay_params": "medium",
        },
        "emotional_telemetry": {
            "rage_clicks": [],
            "caps_lock_aggression": [],
            "detected_frustration_signals": [],
            "sentiment_trends": "stable",
            "latency_focus_integrity": 1.0,
        },
        "current_interaction_context": interaction_context,
        "historical_mastery_map": {
            "active_weakness_arrays": ["algebra"],
            "passed_topics_arrays": ["basic_arithmetic"],
        },
        "learning_session_state": {
            "topic": "algebra",
            "subtopic": "linear_equations",
            "micro_skill": "linear_equations",
            "phase": "practice",
            "attempt": 1,
            "streak": 1,
            "mastery_score": 0.62,
            "state_version": 1,
            "current_question_id": None,
            "last_question_ids": [],
            "correct_pattern": [],
            "response_time_ms": None,
            "confidence_level": "medium",
            "hints_used": 0,
            "difficulty_level": "easy",
            "is_retention_check": False,
        },
    }


def test_free_tier_keeps_one_history_turn_by_default():
    request = NeuralChatRequest.model_validate(
        valid_payload(tier="free", history_tokens=["turn-1", "turn-2", "turn-3"])
    )

    assert request.current_interaction_context.history_tokens == ["turn-3"]


def test_premium_tier_keeps_three_history_turns_by_default():
    request = NeuralChatRequest.model_validate(
        valid_payload(tier="premium", history_tokens=["turn-1", "turn-2", "turn-3", "turn-4"])
    )

    assert request.current_interaction_context.history_tokens == [
        "turn-2",
        "turn-3",
        "turn-4",
    ]


def test_efficiency_mode_drops_history_for_all_tiers():
    request = NeuralChatRequest.model_validate(
        valid_payload(
            tier="premium",
            efficiency_mode=True,
            history_tokens=["turn-1", "turn-2", "turn-3"],
        )
    )

    assert request.current_interaction_context.history_tokens == []


def test_history_limits_are_env_configurable(monkeypatch):
    monkeypatch.setenv("TIER_FREE_MAX_HISTORY_TURNS", "2")

    request = NeuralChatRequest.model_validate(
        valid_payload(tier="free", history_tokens=["turn-1", "turn-2", "turn-3"])
    )

    assert request.current_interaction_context.history_tokens == ["turn-2", "turn-3"]


def test_unknown_tier_is_rejected():
    with pytest.raises(ValidationError):
        NeuralChatRequest.model_validate(valid_payload(tier="enterprise"))


def test_homework_explainer_mode_is_supported():
    request = NeuralChatRequest.model_validate(
        valid_payload(app_execution_mode="homework_explainer")
    )

    assert request.app_execution_mode == "homework_explainer"


def test_correct_answer_is_exam_prep_only():
    with pytest.raises(ValidationError):
        NeuralChatRequest.model_validate(
            valid_payload(
                app_execution_mode="general_prompt",
                raw_whiteboard_input="A",
                correct_answer="A",
            )
        )


def test_correct_answer_requires_selected_option_input():
    with pytest.raises(ValidationError):
        NeuralChatRequest.model_validate(
            valid_payload(
                app_execution_mode="exam_prep",
                raw_whiteboard_input="Solve 2x + 4 = 10",
                correct_answer="A",
            )
        )


def test_correct_answer_allows_exam_prep_option_input():
    request = NeuralChatRequest.model_validate(
        valid_payload(
            app_execution_mode="exam_prep",
            raw_whiteboard_input="A",
            correct_answer="A",
        )
    )

    assert request.current_interaction_context.correct_answer == "A"


def test_blank_transaction_id_is_rejected():
    payload = valid_payload()
    payload["request_metadata"]["uuid_transaction_id"] = "   "

    with pytest.raises(ValidationError):
        NeuralChatRequest.model_validate(payload)


def test_invalid_timestamp_is_rejected():
    payload = valid_payload()
    payload["request_metadata"]["timestamp"] = "tomorrow-ish"

    with pytest.raises(ValidationError):
        NeuralChatRequest.model_validate(payload)


def test_timestamp_requires_timezone():
    payload = valid_payload()
    payload["request_metadata"]["timestamp"] = "2026-05-19T12:00:00"

    with pytest.raises(ValidationError):
        NeuralChatRequest.model_validate(payload)


def test_negative_device_latency_is_rejected():
    payload = valid_payload()
    payload["request_metadata"]["device_latency_ms"] = -1

    with pytest.raises(ValidationError):
        NeuralChatRequest.model_validate(payload)


def test_blank_student_id_is_rejected():
    payload = valid_payload()
    payload["student_identity"]["student_db_id"] = ""

    with pytest.raises(ValidationError):
        NeuralChatRequest.model_validate(payload)


def test_raw_input_length_is_bounded():
    payload = valid_payload(
        raw_whiteboard_input="x" * (MAX_RAW_WHITEBOARD_INPUT_LENGTH + 1)
    )

    with pytest.raises(ValidationError):
        NeuralChatRequest.model_validate(payload)


def test_blank_raw_input_is_rejected():
    payload = valid_payload(raw_whiteboard_input="   ")

    with pytest.raises(ValidationError):
        NeuralChatRequest.model_validate(payload)


def test_history_count_is_bounded_before_tier_trim():
    payload = valid_payload(history_tokens=["turn"] * (MAX_HISTORY_TOKENS + 1))

    with pytest.raises(ValidationError):
        NeuralChatRequest.model_validate(payload)


def test_history_token_length_is_bounded():
    payload = valid_payload(history_tokens=["x" * (MAX_HISTORY_TOKEN_LENGTH + 1)])

    with pytest.raises(ValidationError):
        NeuralChatRequest.model_validate(payload)


def test_mastery_arrays_are_bounded():
    payload = valid_payload()
    payload["historical_mastery_map"]["active_weakness_arrays"] = ["algebra"] * (
        MAX_MASTERY_ITEMS + 1
    )

    with pytest.raises(ValidationError):
        NeuralChatRequest.model_validate(payload)


def test_telemetry_arrays_are_bounded():
    payload = valid_payload()
    payload["emotional_telemetry"]["rage_clicks"] = ["rapid_click"] * (
        MAX_TELEMETRY_EVENTS + 1
    )

    with pytest.raises(ValidationError):
        NeuralChatRequest.model_validate(payload)


def test_low_cardinality_signals_are_normalized():
    payload = valid_payload()
    payload["cognitive_aptitude_profile"]["scaffolding_flag"] = " HIGH "
    payload["cognitive_aptitude_profile"]["complexity_tolerance"] = " LOW "
    payload["emotional_telemetry"]["sentiment_trends"] = " Declining "
    payload["emotional_telemetry"]["detected_frustration_signals"] = [" CONFUSED "]

    request = NeuralChatRequest.model_validate(payload)

    assert request.cognitive_aptitude_profile.scaffolding_flag == "high"
    assert request.cognitive_aptitude_profile.complexity_tolerance == "low"
    assert request.emotional_telemetry.sentiment_trends == "declining"
    assert request.emotional_telemetry.detected_frustration_signals == ["confused"]


def test_unknown_low_cardinality_signal_is_rejected():
    payload = valid_payload()
    payload["cognitive_aptitude_profile"]["scaffolding_flag"] = "extreme"

    with pytest.raises(ValidationError):
        NeuralChatRequest.model_validate(payload)


def test_focus_integrity_must_be_ratio():
    payload = valid_payload()
    payload["emotional_telemetry"]["latency_focus_integrity"] = 1.5

    with pytest.raises(ValidationError):
        NeuralChatRequest.model_validate(payload)
