import json
from pathlib import Path

import pytest

from app.schemas.requests import NeuralChatRequest
from app.services.rag_router import RagContext
from app.services.model_router import ModelRoute
from app.services.strategy.compiler import compile_state_strategy
from app.services.tutor_engine import build_tutor_messages, execute_tutor_response


REPO_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = REPO_ROOT / "data" / "processed" / "concept_registry.json"


@pytest.fixture(autouse=True)
def disable_demo_mode(monkeypatch):
    monkeypatch.setenv("SABI_DEMO_MODE", "false")


def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def model_route() -> ModelRoute:
    return ModelRoute(
        provider_interface="litellm",
        model_env_var="TIER_FREE_MODEL",
        model_name="free-tier-test-model",
        max_history_turns=1,
        execution_path="single_pass",
    )


def build_request(
    *,
    app_execution_mode: str = "general_prompt",
    raw_whiteboard_input: str = "Explain how i go find x for 3x + 1 = 10.",
) -> NeuralChatRequest:
    return NeuralChatRequest.model_validate(
        {
            "request_metadata": {
                "uuid_transaction_id": "txn-tutor-engine-test-001",
                "timestamp": "2026-05-19T12:00:00Z",
                "device_latency_ms": 120,
            },
            "student_identity": {
                "student_db_id": "student_tutor_engine_001",
                "tier": "free",
                "academic_scope": "senior_secondary",
                "exam_target": "WAEC",
            },
            "efficiency_mode": False,
            "app_execution_mode": app_execution_mode,
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


def test_tutor_messages_include_strategy_and_retrieved_context():
    request = build_request(app_execution_mode="exam_prep")
    strategy = compile_state_strategy(request, registry_snapshot=load_registry())
    rag_context = RagContext(
        mode="precision",
        query_concept_key="linear_equations",
        context_text="Question: If 3x + 4 = 19, find x.",
        hits=(),
        source_tags=("src:v1;collection=exam_bank;rank=1",),
    )

    messages = build_tutor_messages(request, strategy, rag_context)
    prompt_text = messages[1]["content"]

    assert messages[0]["role"] == "system"
    assert "normalized_concept=linear_equations" in prompt_text
    assert "teaching_mode=direct_instruction" in prompt_text
    assert "action=explain_step" in prompt_text
    assert "llm_renderer_contract:" in prompt_text
    assert "response_contract:" in prompt_text
    assert "EXPLAIN_STEP:" in prompt_text
    assert "system_selected_practice_question:" in prompt_text
    assert "Question: If 3x + 4 = 19" in prompt_text
    assert "src:v1;collection=exam_bank;rank=1" in prompt_text


def test_tutor_engine_uses_llm_executor_with_injected_completion():
    request = build_request(app_execution_mode="exam_prep")
    strategy = compile_state_strategy(request, registry_snapshot=load_registry())
    rag_context = RagContext(
        mode="precision",
        query_concept_key="linear_equations",
        context_text="Question: If 3x + 4 = 19, find x.",
        hits=(),
        source_tags=(),
    )

    result = execute_tutor_response(
        request=request,
        strategy=strategy,
        rag_context=rag_context,
        model_route=model_route(),
        completion_callable=lambda **_: {
            "choices": [{"message": {"content": "Use inverse operations carefully."}}]
        },
    )

    assert result.text == "Use inverse operations carefully."
    assert result.llm_result is not None
    assert result.used_fallback is False


def test_tutor_engine_returns_pidgin_fallback_when_model_is_unavailable():
    request = build_request(
        app_execution_mode="exam_prep",
        raw_whiteboard_input="Abeg explain how i go find x for this equation.",
    )
    strategy = compile_state_strategy(request, registry_snapshot=load_registry())
    rag_context = RagContext(
        mode="none",
        query_concept_key="linear_equations",
        context_text="",
        hits=(),
        source_tags=(),
    )

    result = execute_tutor_response(
        request=request,
        strategy=strategy,
        rag_context=rag_context,
        model_route=None,
    )

    assert result.used_fallback is True
    assert result.fallback_reason == "model_route_unavailable"
    assert result.text.startswith("No wahala")


def test_tutor_engine_local_fallback_keeps_known_topic_for_subtract_followup():
    request = build_request(
        app_execution_mode="curriculum_coach",
        raw_whiteboard_input="Why do we subtract 4 from both sides in 2x + 4 = 10?",
    )
    strategy = compile_state_strategy(request, registry_snapshot=load_registry())
    rag_context = RagContext(
        mode="none",
        query_concept_key="linear_equations",
        context_text="",
        hits=(),
        source_tags=(),
    )

    result = execute_tutor_response(
        request=request,
        strategy=strategy,
        rag_context=rag_context,
        model_route=None,
    )

    assert result.used_fallback is True
    assert "2x + 4 = 10" in result.text
    assert "did not disappear" in result.text
    assert "Now try:" not in result.text
    assert "Concept:" not in result.text
    assert "Which maths topic" not in result.text


def test_tutor_engine_explains_subtract_step_from_active_history_equation():
    request = build_request(
        app_execution_mode="curriculum_coach",
        raw_whiteboard_input="why are we subtracting 4",
    )
    request.current_interaction_context.history_tokens = [
        "Current question: solve 2x + 4 = 10.",
    ]
    strategy = compile_state_strategy(request, registry_snapshot=load_registry())
    rag_context = RagContext(
        mode="none",
        query_concept_key="linear_equations",
        context_text="",
        hits=(),
        source_tags=(),
    )

    result = execute_tutor_response(
        request=request,
        strategy=strategy,
        rag_context=rag_context,
        model_route=None,
    )

    assert strategy.action_plan.action_type == "explain_step"
    assert strategy.action_plan.state_mutation_allowed is False
    assert "2x + 4 = 10" in result.text
    assert "did not disappear" in result.text
    assert "Linear Equations" not in result.text


def test_tutor_engine_clarifies_without_resetting_known_topic():
    request = build_request(raw_whiteboard_input="Open my profile settings.")
    strategy = compile_state_strategy(request, registry_snapshot=load_registry())
    rag_context = RagContext(
        mode="none",
        query_concept_key=None,
        context_text="",
        hits=(),
        source_tags=(),
    )

    result = execute_tutor_response(
        request=request,
        strategy=strategy,
        rag_context=rag_context,
        model_route=None,
    )

    assert result.used_fallback is True
    assert "Linear Equations" in result.text
    assert "Which maths topic" not in result.text


def test_tutor_engine_demo_mode_bypasses_model_for_supported_quadratic_prompt(
    monkeypatch,
):
    monkeypatch.setenv("SABI_DEMO_MODE", "true")
    request = build_request(
        app_execution_mode="exam_prep",
        raw_whiteboard_input=(
            "I have tried three times. Solve x^2 - 5x + 6 = 0 and explain why "
            "the factors give the roots."
        ),
    )
    strategy = compile_state_strategy(request, registry_snapshot=load_registry())
    rag_context = RagContext(
        mode="none",
        query_concept_key="quadratic_equations",
        context_text="",
        hits=(),
        source_tags=(),
    )

    def fail_completion(**kwargs):
        raise AssertionError("demo-supported prompt should not call the live model")

    result = execute_tutor_response(
        request=request,
        strategy=strategy,
        rag_context=rag_context,
        model_route=model_route(),
        completion_callable=fail_completion,
    )

    assert result.used_fallback is False
    assert result.llm_result is None
    assert result.fallback_reason is None
    assert "x = 2 or x = 3" in result.text


def test_tutor_engine_demo_mode_keeps_live_path_for_unsupported_prompt(monkeypatch):
    monkeypatch.setenv("SABI_DEMO_MODE", "true")
    request = build_request(
        app_execution_mode="general_prompt",
        raw_whiteboard_input="Explain how circle theorems are used in geometry revision.",
    )
    strategy = compile_state_strategy(request, registry_snapshot=load_registry())
    rag_context = RagContext(
        mode="none",
        query_concept_key=None,
        context_text="",
        hits=(),
        source_tags=(),
    )

    result = execute_tutor_response(
        request=request,
        strategy=strategy,
        rag_context=rag_context,
        model_route=model_route(),
        completion_callable=lambda **_: {
            "choices": [{"message": {"content": "Use the live bounded route."}}]
        },
    )

    assert result.text == "Use the live bounded route."
    assert result.llm_result is not None
    assert result.used_fallback is False
