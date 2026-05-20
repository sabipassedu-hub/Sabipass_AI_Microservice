import pytest
from pydantic import ValidationError

from app.schemas.requests import NeuralChatRequest


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
