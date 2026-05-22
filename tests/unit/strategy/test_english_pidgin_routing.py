import json
from pathlib import Path

from app.schemas.requests import NeuralChatRequest
from app.services.strategy.compiler import compile_state_strategy


REPO_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = REPO_ROOT / "data" / "processed" / "concept_registry.json"


def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def build_request(raw_whiteboard_input: str) -> NeuralChatRequest:
    return NeuralChatRequest.model_validate(
        {
            "request_metadata": {
                "uuid_transaction_id": "txn-routing-test-001",
                "timestamp": "2026-05-19T12:00:00Z",
                "device_latency_ms": 120,
            },
            "student_identity": {
                "student_db_id": "student_routing_001",
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
                "raw_whiteboard_input": raw_whiteboard_input,
                "topic_node": "",
                "history_tokens": [],
                "errors_on_same_concept_space": 0,
            },
            "historical_mastery_map": {
                "active_weakness_arrays": ["algebra"],
                "passed_topics_arrays": [],
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
    )


def test_english_linear_equation_prompt_routes_to_precision_strategy():
    strategy = compile_state_strategy(
        build_request("Please explain how to solve for x in this equation."),
        registry_snapshot=load_registry(),
    )

    assert strategy.normalized_concept == "linear_equations"
    assert strategy.normalization_status == "strict"
    assert strategy.pedagogy_strategy.intent_type == "explanation"
    assert strategy.rag_strategy.mode == "precision"
    assert strategy.rag_strategy.target_collection == "exam_bank"


def test_pidgin_linear_equation_prompt_routes_to_same_precision_strategy():
    strategy = compile_state_strategy(
        build_request("Abeg explain how i go find x for this equation."),
        registry_snapshot=load_registry(),
    )

    assert strategy.normalized_concept == "linear_equations"
    assert strategy.normalization_status == "strict"
    assert strategy.pedagogy_strategy.intent_type == "explanation"
    assert strategy.rag_strategy.mode == "precision"
    assert strategy.rag_strategy.filter_dict["topic"] == "linear_equations"
