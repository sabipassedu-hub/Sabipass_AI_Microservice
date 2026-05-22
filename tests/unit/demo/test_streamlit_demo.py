from importlib import import_module

from app.schemas.requests import NeuralChatRequest


def test_demo_builds_canonical_node_payload():
    demo = import_module("streamlit_test.app")

    payload = demo.build_neural_chat_payload(
        student_input="How I go solve 2x + 4 = 10?",
        tier="premium",
        efficiency_mode=True,
    )

    NeuralChatRequest.model_validate(payload)
    assert payload["student_identity"]["tier"] == "premium"
    assert payload["efficiency_mode"] is True
    assert payload["app_execution_mode"] == "exam_prep"
    assert payload["current_interaction_context"]["raw_whiteboard_input"] == (
        "How I go solve 2x + 4 = 10?"
    )
    assert "uuid_transaction_id" in payload["request_metadata"]
    assert payload["request_metadata"]["timestamp"].endswith("Z")


def test_demo_defaults_student_payload_to_freemium():
    demo = import_module("streamlit_test.app")

    payload = demo.build_neural_chat_payload(
        student_input="Explain linear equations for SS1 Term 1.",
        app_execution_mode="curriculum_coach",
        academic_scope="senior_secondary_1",
    )

    NeuralChatRequest.model_validate(payload)
    assert payload["student_identity"]["tier"] == "free"
    assert payload["app_execution_mode"] == "curriculum_coach"


def test_demo_declares_vc_modes_and_locked_premium_model():
    demo = import_module("streamlit_test.app")

    modes = {mode.key: mode.app_execution_mode for mode in demo.STUDY_MODES}
    assert modes == {
        "curriculum": "curriculum_coach",
        "homework": "homework_explainer",
        "exam": "exam_prep",
    }
    assert demo.MODEL_OPTIONS_BY_KEY[demo.DEFAULT_MODEL_KEY].label == "Gemini"
    assert demo.MODEL_OPTIONS_BY_KEY[demo.LOCKED_MODEL_KEY].locked is True
    assert demo.MODEL_OPTIONS_BY_KEY[demo.LOCKED_MODEL_KEY].badge == "Premium"
    assert demo.DEFAULT_STUDY_MODE_KEY == "exam"
    assert "pass" not in " ".join(demo.PIPELINE_LABELS.values()).lower()


def test_demo_posts_to_fastapi_endpoint(monkeypatch):
    demo = import_module("streamlit_test.app")
    calls = []

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"tutor_conversational_text": "Socratic tutor placeholder text response."}

    def fake_post(url, *, json, timeout):
        calls.append({"url": url, "json": json, "timeout": timeout})
        return FakeResponse()

    monkeypatch.setattr(demo.requests, "post", fake_post)

    response = demo.post_neural_chat(
        api_url="http://127.0.0.1:8000/api/v1/neural/chat",
        payload=demo.build_neural_chat_payload(
            student_input="Solve 2x + 4 = 10",
            tier="free",
            efficiency_mode=False,
        ),
    )

    assert response["tutor_conversational_text"]
    assert calls[0]["url"] == "http://127.0.0.1:8000/api/v1/neural/chat"
    assert calls[0]["json"]["student_identity"]["tier"] == "free"
    assert calls[0]["timeout"] == demo.REQUEST_TIMEOUT_SECONDS
    assert demo.REQUEST_TIMEOUT_SECONDS <= 10


def test_demo_builds_free_premium_and_efficiency_routing_payloads():
    demo = import_module("streamlit_test.app")

    payloads = demo.build_routing_verification_payloads()

    assert [
        (payload["student_identity"]["tier"], payload["efficiency_mode"])
        for payload in payloads
    ] == [
        ("free", False),
        ("premium", False),
        ("premium", True),
    ]
    for payload in payloads:
        NeuralChatRequest.model_validate(payload)
        assert payload["current_interaction_context"]["topic_node"] == "quadratic_equations"
        assert payload["current_interaction_context"]["errors_on_same_concept_space"] == 3

    assert payloads[0]["current_interaction_context"]["history_tokens"]
    assert payloads[1]["current_interaction_context"]["history_tokens"]
    assert payloads[2]["current_interaction_context"]["history_tokens"] == []


def test_demo_summarizes_routing_metadata_from_response():
    demo = import_module("streamlit_test.app")
    payload = demo.build_neural_chat_payload(
        student_input="Solve x^2 - 5x + 6 = 0",
        tier="premium",
        efficiency_mode=False,
    )

    row = demo.summarize_routing_result(
        payload=payload,
        response_data={
            "system_metadata": {
                "model_env_var": "TIER_PREMIUM_MODEL",
                "model_name": "premium-tier-test-model",
                "model_execution_path": "two_pass",
                "normalized_concept": "quadratic_equations",
                "llm_status": "completed",
            }
        },
    )

    assert row == {
        "tier": "premium",
        "efficiency_mode": False,
        "history_turns_sent": 2,
        "model_env_var": "TIER_PREMIUM_MODEL",
        "execution_path": "two_pass",
        "normalized_concept": "quadratic_equations",
        "llm_status": "completed",
    }


def test_demo_verifies_routing_matrix_by_posting_three_payloads(monkeypatch):
    demo = import_module("streamlit_test.app")
    calls = []

    def fake_post_neural_chat(*, api_url, payload):
        calls.append({"api_url": api_url, "payload": payload})
        if payload["efficiency_mode"]:
            model_env_var = "EFFICIENCY_MODE_MODEL"
            execution_path = "single_pass"
        elif payload["student_identity"]["tier"] == "premium":
            model_env_var = "TIER_PREMIUM_MODEL"
            execution_path = "two_pass"
        else:
            model_env_var = "TIER_FREE_MODEL"
            execution_path = "single_pass"

        return {
            "system_metadata": {
                "model_env_var": model_env_var,
                "model_name": f"{model_env_var.lower()}-resolved",
                "model_execution_path": execution_path,
                "normalized_concept": "quadratic_equations",
                "llm_status": "completed",
            }
        }

    monkeypatch.setattr(demo, "post_neural_chat", fake_post_neural_chat)

    rows = demo.verify_routing_matrix(api_url="http://127.0.0.1:8000/api/v1/neural/chat")

    assert len(calls) == 3
    assert [row["model_env_var"] for row in rows] == [
        "TIER_FREE_MODEL",
        "TIER_PREMIUM_MODEL",
        "EFFICIENCY_MODE_MODEL",
    ]
    assert [row["execution_path"] for row in rows] == [
        "single_pass",
        "two_pass",
        "single_pass",
    ]


def test_demo_status_labels_are_student_and_investor_safe():
    demo = import_module("streamlit_test.app")

    safe_status = demo._safe_response_status(
        {
            "system_metadata": {
                "llm_status": "not_needed_deterministic",
                "demo_response_status": "deterministic_supported_prompt",
            }
        },
        elapsed_ms=42,
    )
    outage_status = demo._safe_response_status(
        {
            "system_metadata": {
                "pipeline_status": "request_failed",
                "llm_status": "ReadTimeout",
            }
        }
    )

    assert safe_status["label"] == "Demo-Safe Response"
    assert "deterministic_supported_prompt" not in safe_status["detail"]
    assert "ReadTimeout" not in outage_status["detail"]
    assert outage_status["label"] == "Connection Needed"


def test_demo_operator_summary_filters_provider_and_trace_internals():
    demo = import_module("streamlit_test.app")

    summary = demo._safe_operator_response(
        {
            "request_id": "txn-demo",
            "response_type": "text_only",
            "is_atomic": True,
            "error": "provider stack trace",
            "system_metadata": {
                "model_name": "raw-provider-model",
                "model_env_var": "TIER_FREE_MODEL",
                "llm_fallback_reason": "llm_provider_error",
                "normalized_concept": "linear_equations",
                "llm_status": "local_fallback",
                "demo_response_status": "safety_fallback",
            },
        }
    )

    metadata = summary["system_metadata"]
    assert "error" not in summary
    assert "model_name" not in metadata
    assert "model_env_var" not in metadata
    assert "llm_fallback_reason" not in metadata
    assert metadata["normalized_concept"] == "linear_equations"
