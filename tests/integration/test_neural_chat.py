import logging

import pytest
from fastapi.testclient import TestClient
from main import app
from app.api.v1.routes.neural_chat import get_chroma_collections
from app.observability.trace_buffer import configure_trace_buffer, get_trace_buffer

client = TestClient(app)


def _learning_state(subtopic: str = "linear_equations") -> dict:
    return {
        "topic": "algebra",
        "subtopic": subtopic,
        "micro_skill": subtopic,
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
    }

def test_neural_chat_contract_enforcement():
    valid_payload = {
        "request_metadata": {
            "transaction_id": "abc-123-uuid",
            "timestamp": "2026-05-14T15:00:00Z",
            "client_latency_ms": 140
        },
        "student_identity": {
            "student_id": "student_tunde_01",
            "subscription_tier": "free",
            "academic_stage": "senior_secondary_2",
            "target_examination": "WAEC 2027"
        },
        "cognitive_aptitude_profile": {
            "learning_velocity_index": 0.72,
            "scaffolding_dependency": "low",
            "complexity_tolerance": "high",
            "retention_decay_rate": "medium"
        },
        "emotional_telemetry": {
            "detected_frustration_signals": ["rage_clicks"],
            "session_sentiment_trend": "stable",
            "focus_integrity_score": 0.82
        },
        "current_interaction_context": {
            "user_input_text": "Solve 2x + 4 = 10",
            "active_topic_node": "linear_equations",
            "previous_bot_response_id": "init",
            "attempt_count_on_current_concept": 1
        },
        "historical_mastery_map": {
            "known_weaknesses": ["algebra"],
            "mastered_strengths": ["basic_arithmetic"]
        },
        "learning_session_state": _learning_state()
    }
    
    response = client.post("/api/v1/neural/chat", json=valid_payload)
    assert response.status_code == 200
    
    data = response.json()
    
    # TYPE-SAFE CONTRACT ENFORCEMENT
    assert "tutor_conversational_text" in data
    assert isinstance(data["tutor_conversational_text"], str)
    
    assert "neural_sync_payload" in data
    assert isinstance(data["neural_sync_payload"], dict)
    
    assert "canvas_directive" in data
    assert data["canvas_directive"] is None or isinstance(data["canvas_directive"], dict)
    
    assert "micro_rewards" in data
    assert data["micro_rewards"] is None or isinstance(data["micro_rewards"], dict)


def test_neural_chat_zero_pass_returns_node_compatible_mcq_response():
    payload = {
        "request_metadata": {
            "uuid_transaction_id": "txn-zero-pass-route-001",
            "timestamp": "2026-05-14T15:00:00Z",
            "device_latency_ms": 140
        },
        "student_identity": {
            "student_id": "student_tunde_01",
            "subscription_tier": "free",
            "academic_stage": "senior_secondary_2",
            "target_examination": "WAEC 2027"
        },
        "app_execution_mode": "exam_prep",
        "cognitive_aptitude_profile": {
            "learning_velocity_index": 0.72,
            "scaffolding_dependency": "low",
            "complexity_tolerance": "high",
            "retention_decay_rate": "medium"
        },
        "emotional_telemetry": {
            "detected_frustration_signals": [],
            "session_sentiment_trend": "stable",
            "focus_integrity_score": 0.82
        },
        "current_interaction_context": {
            "user_input_text": "B",
            "active_topic_node": "quadratic_equations",
            "previous_bot_response_id": "init",
            "attempt_count_on_current_concept": 1,
            "correct_answer": "C"
        },
        "historical_mastery_map": {
            "known_weaknesses": ["algebra"],
            "mastered_strengths": ["basic_arithmetic"]
        },
        "learning_session_state": _learning_state("quadratic_equations")
    }

    app.dependency_overrides[get_chroma_collections] = lambda: {}
    try:
        response = client.post("/api/v1/neural/chat", json=payload)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()

    assert data["response_type"] == "zero_pass_response"
    assert data["is_atomic"] is True
    assert data["canvas_directive"] is None
    assert isinstance(data["neural_sync_payload"], dict)
    assert data["system_metadata"]["pipeline_status"] == "zero_pass_completed"
    assert data["system_metadata"]["rag_status"] == "not_started"
    assert data["system_metadata"]["model_status"] == "not_started"
    assert data["system_metadata"]["zero_pass_reason"] == "zero_pass_mcq_incorrect"


def test_neural_chat_records_trace_and_metrics_for_zero_pass(caplog):
    configure_trace_buffer(5)
    caplog.set_level(logging.INFO, logger="sabipass.metrics")
    payload = {
        "request_metadata": {
            "uuid_transaction_id": "txn-zero-pass-observable-001",
            "timestamp": "2026-05-14T15:00:00Z",
            "device_latency_ms": 140
        },
        "student_identity": {
            "student_id": "student_tunde_01",
            "subscription_tier": "free",
            "academic_stage": "senior_secondary_2",
            "target_examination": "WAEC 2027"
        },
        "app_execution_mode": "exam_prep",
        "cognitive_aptitude_profile": {
            "learning_velocity_index": 0.72,
            "scaffolding_dependency": "low",
            "complexity_tolerance": "high",
            "retention_decay_rate": "medium"
        },
        "emotional_telemetry": {
            "detected_frustration_signals": [],
            "session_sentiment_trend": "stable",
            "focus_integrity_score": 0.82
        },
        "current_interaction_context": {
            "user_input_text": "B",
            "active_topic_node": "quadratic_equations",
            "previous_bot_response_id": "init",
            "attempt_count_on_current_concept": 1,
            "correct_answer": "C"
        },
        "historical_mastery_map": {
            "known_weaknesses": ["algebra"],
            "mastered_strengths": ["basic_arithmetic"]
        },
        "learning_session_state": _learning_state("quadratic_equations")
    }

    app.dependency_overrides[get_chroma_collections] = lambda: {}
    try:
        response = client.post("/api/v1/neural/chat", json=payload)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    trace = get_trace_buffer().snapshot()[-1]
    assert trace.request_id == "txn-zero-pass-observable-001"
    assert trace.request_status == "completed"
    assert trace.registry_version == "1.0"
    assert trace.rag_status == "not_started"
    assert trace.model_status == "not_started"
    assert trace.llm_fallback_reason == "zero_pass_mcq_incorrect"
    assert trace.zero_pass_reason == "zero_pass_mcq_incorrect"
    assert "sabi.request.total" in caplog.text
    assert "sabi.fallback.reason" in caplog.text
