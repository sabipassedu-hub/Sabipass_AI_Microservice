import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.routes import neural_chat as neural_chat_route
from app.api.v1.routes.neural_chat import (
    get_chroma_collections,
    get_llm_completion_callable,
)
from app.core import lifespan as lifespan_module
from app.db.chroma import initialize_chroma
from main import app
from pipelines.ingestion.chroma_seed import seed_mock_exam_bank
from streamlit_test.app import build_routing_verification_payloads


REPO_ROOT = Path(__file__).resolve().parents[2]
MOCK_RAW_DIR = REPO_ROOT / "data" / "raw" / "mock"
_MISSING = object()


@pytest.fixture(autouse=True)
def disable_demo_mode(monkeypatch):
    monkeypatch.setenv("SABI_DEMO_MODE", "false")


def test_lifespan_initializes_rag_state_and_demo_warmup(monkeypatch):
    fake_collections = {"exam_bank": object()}

    monkeypatch.setattr(
        lifespan_module,
        "get_settings",
        lambda: SimpleNamespace(sabi_bootstrap_mock_data=True),
    )
    monkeypatch.setattr(lifespan_module, "initialize_chroma", lambda: fake_collections)
    monkeypatch.setattr(lifespan_module, "warm_embedding_model", lambda: "warm-model")
    monkeypatch.setattr(lifespan_module, "seed_demo_collections", lambda: "seeded")

    test_app = FastAPI()

    async def run_lifespan():
        async with lifespan_module.lifespan(test_app):
            assert test_app.state.sabi_chroma_collections is fake_collections
            assert test_app.state.sabi_embed_query is lifespan_module.embed_query_text
            assert test_app.state.sabi_embedding_model_name == "warm-model"
            assert test_app.state.sabi_demo_seed_result == "seeded"

    asyncio.run(run_lifespan())


def test_neural_chat_uses_lifespan_chroma_state_without_route_initialization(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("TIER_FREE_MODEL", "free-demo-model")
    seed_mock_exam_bank(MOCK_RAW_DIR, storage_path=tmp_path)
    captured_calls = []

    def fake_completion(**kwargs):
        captured_calls.append(kwargs)
        return {"choices": [{"message": {"content": "Use the state-backed context."}}]}

    previous_collections = _replace_app_state(
        "sabi_chroma_collections",
        initialize_chroma(tmp_path),
    )
    previous_embed_query = _replace_app_state(
        "sabi_embed_query",
        neural_chat_route.embed_query_text,
    )

    def fail_initialize_chroma():
        raise AssertionError("request path must use lifespan Chroma collections")

    monkeypatch.setattr(
        neural_chat_route,
        "initialize_chroma",
        fail_initialize_chroma,
    )
    app.dependency_overrides[get_llm_completion_callable] = lambda: fake_completion
    try:
        response = TestClient(app).post(
            "/api/v1/neural/chat",
            json=_payload("Please explain how to solve for x in this equation."),
        )
    finally:
        app.dependency_overrides.clear()
        _restore_app_state("sabi_chroma_collections", previous_collections)
        _restore_app_state("sabi_embed_query", previous_embed_query)

    assert response.status_code == 200
    data = response.json()
    assert data["tutor_conversational_text"] == "Use the state-backed context."
    assert data["system_metadata"]["rag_status"] == "completed"
    assert captured_calls


def test_neural_chat_wires_strategy_rag_model_and_llm_for_english_prompt(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("TIER_FREE_MODEL", "free-demo-model")
    seed_mock_exam_bank(MOCK_RAW_DIR, storage_path=tmp_path)
    captured_calls = []

    def fake_completion(**kwargs):
        captured_calls.append(kwargs)
        return {
            "choices": [
                {
                    "message": {
                        "content": (
                            "Start by isolating x: subtract the constant term, "
                            "then divide by the coefficient and check the value."
                        )
                    }
                }
            ]
        }

    app.dependency_overrides[get_chroma_collections] = lambda: initialize_chroma(tmp_path)
    app.dependency_overrides[get_llm_completion_callable] = lambda: fake_completion
    try:
        response = TestClient(app).post(
            "/api/v1/neural/chat",
            json=_payload("Please explain how to solve for x in this equation."),
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert "subtract the constant term" in data["tutor_conversational_text"]
    assert data["response_type"] == "text_only"
    assert data["system_metadata"]["pipeline_status"] == "wired"
    assert data["system_metadata"]["normalized_concept"] == "linear_equations"
    assert data["system_metadata"]["rag_mode"] == "precision"
    assert data["system_metadata"]["model_env_var"] == "TIER_FREE_MODEL"
    assert data["system_metadata"]["model_name"] == "free-demo-model"
    assert data["system_metadata"]["llm_status"] == "completed"

    prompt_text = captured_calls[0]["messages"][1]["content"]
    assert captured_calls[0]["model"] == "free-demo-model"
    assert "normalized_concept=linear_equations" in prompt_text
    assert "Question: If 3x + 4 = 19" in prompt_text
    assert "teaching_mode=direct_instruction" in prompt_text


def test_neural_chat_returns_pidgin_aware_waec_math_response(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("TIER_FREE_MODEL", "free-demo-model")
    seed_mock_exam_bank(MOCK_RAW_DIR, storage_path=tmp_path)
    captured_calls = []

    def fake_completion(**kwargs):
        captured_calls.append(kwargs)
        prompt_text = kwargs["messages"][1]["content"]
        assert "Pidgin" in prompt_text
        return {
            "choices": [
                {
                    "message": {
                        "content": (
                            "No wahala. First move the constant to the other side, "
                            "then divide by the number beside x."
                        )
                    }
                }
            ]
        }

    app.dependency_overrides[get_chroma_collections] = lambda: initialize_chroma(tmp_path)
    app.dependency_overrides[get_llm_completion_callable] = lambda: fake_completion
    try:
        response = TestClient(app).post(
            "/api/v1/neural/chat",
            json=_payload("Abeg explain how i go find x for this equation."),
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["tutor_conversational_text"].startswith("No wahala")
    assert data["system_metadata"]["normalized_concept"] == "linear_equations"
    assert data["system_metadata"]["rag_mode"] == "precision"
    assert data["system_metadata"]["llm_status"] == "completed"
    assert captured_calls


def test_streamlit_routing_payloads_exercise_free_premium_and_efficiency_routes(
    monkeypatch,
):
    monkeypatch.setenv("TIER_FREE_MODEL", "free-demo-model")
    monkeypatch.setenv("TIER_PREMIUM_MODEL", "premium-demo-model")
    monkeypatch.setenv("EFFICIENCY_MODE_MODEL", "efficiency-demo-model")
    captured_models = []

    def fake_completion(**kwargs):
        captured_models.append(kwargs["model"])
        return {"choices": [{"message": {"content": "Use the verified strategy."}}]}

    app.dependency_overrides[get_chroma_collections] = lambda: {}
    app.dependency_overrides[get_llm_completion_callable] = lambda: fake_completion
    try:
        client = TestClient(app)
        responses = [
            client.post("/api/v1/neural/chat", json=payload)
            for payload in build_routing_verification_payloads()
        ]
    finally:
        app.dependency_overrides.clear()

    assert [response.status_code for response in responses] == [200, 200, 200]
    metadata = [response.json()["system_metadata"] for response in responses]
    assert [item["model_env_var"] for item in metadata] == [
        "TIER_FREE_MODEL",
        "TIER_PREMIUM_MODEL",
        "EFFICIENCY_MODE_MODEL",
    ]
    assert [item["model_name"] for item in metadata] == [
        "free-demo-model",
        "premium-demo-model",
        "efficiency-demo-model",
    ]
    assert [item["model_execution_path"] for item in metadata] == [
        "single_pass",
        "two_pass",
        "single_pass",
    ]
    assert captured_models == [
        "free-demo-model",
        "premium-demo-model",
        "efficiency-demo-model",
    ]


def test_demo_mode_route_matrix_uses_deterministic_supported_prompts(monkeypatch):
    monkeypatch.setenv("SABI_DEMO_MODE", "true")
    monkeypatch.setenv("TIER_FREE_MODEL", "free-demo-model")
    monkeypatch.setenv("TIER_PREMIUM_MODEL", "premium-demo-model")
    monkeypatch.setenv("EFFICIENCY_MODE_MODEL", "efficiency-demo-model")

    def fail_completion(**kwargs):
        raise AssertionError("supported VC demo prompts should bypass the live model")

    app.dependency_overrides[get_chroma_collections] = lambda: {}
    app.dependency_overrides[get_llm_completion_callable] = lambda: fail_completion
    try:
        client = TestClient(app)
        responses = [
            client.post("/api/v1/neural/chat", json=payload)
            for payload in build_routing_verification_payloads()
        ]
    finally:
        app.dependency_overrides.clear()

    assert [response.status_code for response in responses] == [200, 200, 200]
    metadata = [response.json()["system_metadata"] for response in responses]
    assert [item["llm_status"] for item in metadata] == [
        "not_needed_deterministic",
        "not_needed_deterministic",
        "not_needed_deterministic",
    ]
    assert [item["demo_response_status"] for item in metadata] == [
        "deterministic_supported_prompt",
        "deterministic_supported_prompt",
        "deterministic_supported_prompt",
    ]
    assert all("x = 2 or x = 3" in response.json()["tutor_conversational_text"] for response in responses)


def _replace_app_state(name: str, value):
    previous = getattr(app.state, name, _MISSING)
    setattr(app.state, name, value)
    return previous


def _restore_app_state(name: str, previous):
    if previous is _MISSING:
        if hasattr(app.state, name):
            delattr(app.state, name)
        return

    setattr(app.state, name, previous)


def _payload(raw_whiteboard_input: str) -> dict:
    return {
        "request_metadata": {
            "uuid_transaction_id": f"txn-{abs(hash(raw_whiteboard_input))}",
            "timestamp": "2026-05-19T12:00:00Z",
            "device_latency_ms": 120,
        },
        "student_identity": {
            "student_db_id": "student_pipeline_001",
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
