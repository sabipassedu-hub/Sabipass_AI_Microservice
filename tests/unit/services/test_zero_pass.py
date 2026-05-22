from app.schemas.requests import NeuralChatRequest
from app.services.zero_pass import evaluate_zero_pass


def build_request(*, selected_answer: str = "C", correct_answer: str | None = "C"):
    payload = {
        "request_metadata": {
            "uuid_transaction_id": "txn-zero-pass-001",
            "timestamp": "2026-05-19T12:00:00Z",
            "device_latency_ms": 120,
        },
        "student_identity": {
            "student_db_id": "student_zero_pass_001",
            "tier": "free",
            "academic_scope": "senior_secondary",
            "exam_target": "WAEC",
        },
        "efficiency_mode": False,
        "app_execution_mode": "exam_prep",
        "cognitive_aptitude_profile": {
            "regression_slope": 0.2,
            "scaffolding_flag": "low",
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
        "current_interaction_context": {
            "raw_whiteboard_input": selected_answer,
            "topic_node": "quadratic_equations",
            "history_tokens": [],
            "errors_on_same_concept_space": 0,
            "correct_answer": correct_answer,
        },
        "historical_mastery_map": {
            "active_weakness_arrays": ["quadratic_equations"],
            "passed_topics_arrays": [],
        },
        "learning_session_state": {
            "topic": "algebra",
            "subtopic": "quadratic_equations",
            "micro_skill": "quadratic_equations",
            "phase": "evaluation",
            "attempt": 1,
            "streak": 1,
            "mastery_score": 0.68,
            "state_version": 1,
            "current_question_id": "waec_quadratic_001",
            "last_question_ids": ["waec_quadratic_001"],
            "correct_pattern": [],
            "response_time_ms": 4500,
            "confidence_level": "medium",
            "hints_used": 0,
            "difficulty_level": "medium",
            "is_retention_check": False,
        },
    }
    if correct_answer is None:
        del payload["current_interaction_context"]["correct_answer"]
    return NeuralChatRequest.model_validate(payload)


def test_zero_pass_returns_correct_mcq_feedback():
    result = evaluate_zero_pass(build_request(selected_answer="c", correct_answer="C"))

    assert result is not None
    assert result.is_correct is True
    assert result.status == "correct"
    assert result.reason == "zero_pass_mcq_correct"
    assert result.micro_rewards["praise_type"] == "accuracy"
    assert result.concept_key == "quadratic_equations"


def test_zero_pass_returns_incorrect_mcq_feedback():
    result = evaluate_zero_pass(build_request(selected_answer="B", correct_answer="C"))

    assert result is not None
    assert result.is_correct is False
    assert result.status == "incorrect"
    assert result.reason == "zero_pass_mcq_incorrect"
    assert "You chose B" in result.tutor_text
    assert "correct answer is C" in result.tutor_text


def test_zero_pass_ignores_non_mcq_requests_without_answer_key():
    assert evaluate_zero_pass(build_request(correct_answer=None)) is None
