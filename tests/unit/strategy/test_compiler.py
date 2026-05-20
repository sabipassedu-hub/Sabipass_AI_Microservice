import json
from pathlib import Path

from app.schemas.requests import NeuralChatRequest
from app.services.strategy.compiler import compile_state_strategy


REPO_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = REPO_ROOT / "data" / "processed" / "concept_registry.json"


def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def valid_payload(
    *,
    tier: str = "free",
    efficiency_mode: bool = False,
    app_execution_mode: str = "general_prompt",
    raw_whiteboard_input: str = "Explain how i go find x for 3x + 1 = 10.",
    topic_node: str = "",
    errors_on_same_concept_space: int = 0,
    detected_frustration_signals: list[str] | None = None,
    sentiment_trends: str = "stable",
    scaffolding_flag: str = "low",
    complexity_tolerance: str = "medium",
) -> dict:
    return {
        "request_metadata": {
            "uuid_transaction_id": "txn-strategy-test-001",
            "timestamp": "2026-05-19T12:00:00Z",
            "device_latency_ms": 120,
        },
        "student_identity": {
            "student_db_id": "student_strategy_001",
            "tier": tier,
            "academic_scope": "senior_secondary",
            "exam_target": "WAEC",
        },
        "efficiency_mode": efficiency_mode,
        "app_execution_mode": app_execution_mode,
        "cognitive_aptitude_profile": {
            "regression_slope": 0.2,
            "scaffolding_flag": scaffolding_flag,
            "complexity_tolerance": complexity_tolerance,
            "knowledge_decay_params": "medium",
        },
        "emotional_telemetry": {
            "rage_clicks": [],
            "caps_lock_aggression": [],
            "detected_frustration_signals": detected_frustration_signals or [],
            "sentiment_trends": sentiment_trends,
            "latency_focus_integrity": 1.0,
        },
        "current_interaction_context": {
            "raw_whiteboard_input": raw_whiteboard_input,
            "topic_node": topic_node,
            "history_tokens": [],
            "errors_on_same_concept_space": errors_on_same_concept_space,
        },
        "historical_mastery_map": {
            "active_weakness_arrays": ["algebra"],
            "passed_topics_arrays": ["fractions_decimals_percentages"],
        },
    }


def build_request(**overrides) -> NeuralChatRequest:
    return NeuralChatRequest.model_validate(valid_payload(**overrides))


def test_compile_state_strategy_builds_precision_strategy_from_strict_concept():
    strategy = compile_state_strategy(build_request(app_execution_mode="exam_prep"), registry_snapshot=load_registry())

    assert strategy.execution_path == "single_pass"
    assert strategy.complexity_score == 3
    assert strategy.normalized_concept == "linear_equations"
    assert strategy.normalization_status == "strict"
    assert strategy.rag_strategy.mode == "precision"
    assert strategy.rag_strategy.target_collection == "exam_bank"
    assert strategy.rag_strategy.query_concept_key == "linear_equations"
    assert strategy.rag_strategy.filter_dict == {
        "subject": "mathematics",
        "topic": "linear_equations",
        "exam_type": "WAEC",
        "academic_stage": "senior_secondary",
    }
    assert strategy.pedagogy_strategy.intent_type == "explanation"
    assert strategy.pedagogy_strategy.teaching_mode == "direct_instruction"
    assert strategy.model_strategy.tier == "free"


def test_compile_state_strategy_allows_premium_two_pass_for_high_complexity():
    request = build_request(
        tier="premium",
        raw_whiteboard_input=(
            "I have tried three times. Solve x^2 - 5x + 6 = 0 "
            "and explain why the factors give the roots."
        ),
        errors_on_same_concept_space=3,
        detected_frustration_signals=["confused", "stuck"],
        sentiment_trends="declining",
        scaffolding_flag="high",
        complexity_tolerance="low",
    )

    strategy = compile_state_strategy(request, registry_snapshot=load_registry())

    assert strategy.execution_path == "two_pass"
    assert strategy.complexity_score == 5
    assert strategy.model_strategy.execution_path == "two_pass"


def test_compile_state_strategy_uses_fallback_for_degraded_math_concept():
    request = build_request(raw_whiteboard_input="I need help with this mathematics question from class.")

    strategy = compile_state_strategy(request, registry_snapshot=load_registry())

    assert strategy.normalized_concept == "general_mathematics"
    assert strategy.normalization_status == "degraded"
    assert strategy.rag_strategy.mode == "fallback"
    assert strategy.rag_strategy.target_collection is None
    assert strategy.rag_strategy.top_k == 0


def test_compile_state_strategy_requests_clarification_for_non_math_prompt():
    request = build_request(raw_whiteboard_input="Open my profile settings.")

    strategy = compile_state_strategy(request, registry_snapshot=load_registry())

    assert strategy.normalized_concept is None
    assert strategy.normalization_status == "needs_clarification"
    assert strategy.rag_strategy.mode == "none"
    assert strategy.pedagogy_strategy.teaching_mode == "clarification"
    assert strategy.pedagogy_strategy.response_format == "micro_clarification"
