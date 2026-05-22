from copy import deepcopy

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def _valid_payload() -> dict:
    return {
        "request_metadata": {
            "uuid_transaction_id": "txn-invalid-payload-001",
            "timestamp": "2026-05-19T12:00:00Z",
            "device_latency_ms": 120,
        },
        "student_identity": {
            "student_db_id": "student_invalid_payload_001",
            "tier": "free",
            "academic_scope": "senior_secondary_2",
            "exam_target": "WAEC",
        },
        "efficiency_mode": False,
        "app_execution_mode": "general_prompt",
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
        "current_interaction_context": {
            "raw_whiteboard_input": "Solve 2x + 4 = 10",
            "topic_node": "linear_equations",
            "history_tokens": [],
            "errors_on_same_concept_space": 0,
        },
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


def test_invalid_payload_rejection():
    """
    Guarantees that empty or structurally malformed data objects
    are cleanly blocked by our contract layer with a 422 error.
    """
    # Sending a completely blank payload to test boundary defenses
    response = client.post("/api/v1/neural/chat", json={})
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("request_metadata", "uuid_transaction_id"), ""),
        (("request_metadata", "timestamp"), "not-a-timestamp"),
        (("request_metadata", "device_latency_ms"), -1),
        (("current_interaction_context", "raw_whiteboard_input"), "x" * 4_001),
        (("current_interaction_context", "history_tokens"), ["turn"] * 51),
        (("historical_mastery_map", "active_weakness_arrays"), ["algebra"] * 51),
        (("emotional_telemetry", "rage_clicks"), ["rapid_click"] * 51),
        (("emotional_telemetry", "sentiment_trends"), "chaotic"),
    ],
)
def test_schema_valid_but_unsafe_payloads_return_422(path, value):
    payload = deepcopy(_valid_payload())
    cursor = payload
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = value

    response = client.post("/api/v1/neural/chat", json=payload)

    assert response.status_code == 422
