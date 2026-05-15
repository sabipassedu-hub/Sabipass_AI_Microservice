import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

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
            "focus_integrity_score": 82.0
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
        }
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
