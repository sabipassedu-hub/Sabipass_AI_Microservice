import ast
from pathlib import Path

import pytest

from app.services.llm_executor import (
    LLMExecutionRequest,
    LLMExecutionResult,
    execute_llm_call,
)
from app.services.model_router import ModelRoute


def model_route() -> ModelRoute:
    return ModelRoute(
        provider_interface="litellm",
        model_env_var="TIER_FREE_MODEL",
        model_name="free-tier-test-model",
        max_history_turns=1,
        execution_path="single_pass",
    )


def test_llm_executor_calls_litellm_compatible_completion_callable():
    captured_kwargs = {}

    def fake_completion(**kwargs):
        captured_kwargs.update(kwargs)
        return {
            "choices": [
                {
                    "message": {
                        "content": "Use inverse operations, then check the answer."
                    }
                }
            ]
        }

    request = LLMExecutionRequest(
        route=model_route(),
        messages=({"role": "user", "content": "Solve 2x = 6"},),
        temperature=0.1,
        max_tokens=64,
    )

    result = execute_llm_call(request, completion_callable=fake_completion)

    assert captured_kwargs == {
        "model": "free-tier-test-model",
        "messages": [{"role": "user", "content": "Solve 2x = 6"}],
        "temperature": 0.1,
        "max_tokens": 64,
    }
    assert result == LLMExecutionResult(
        text="Use inverse operations, then check the answer.",
        model="free-tier-test-model",
        provider_interface="litellm",
        execution_path="single_pass",
    )


def test_llm_execution_request_rejects_empty_messages():
    with pytest.raises(ValueError, match="messages"):
        LLMExecutionRequest(route=model_route(), messages=())


def test_llm_executor_rejects_non_litellm_routes():
    request = LLMExecutionRequest(
        route=ModelRoute(
            provider_interface="direct_provider",
            model_env_var="DIRECT_PROVIDER_MODEL",
            model_name="direct-model",
            max_history_turns=1,
            execution_path="single_pass",
        ),
        messages=({"role": "user", "content": "Solve 2x = 6"},),
    )

    with pytest.raises(ValueError, match="LiteLLM"):
        execute_llm_call(request, completion_callable=lambda **_: {})


def test_llm_executor_does_not_import_direct_provider_sdks():
    source_path = Path(__file__).resolve().parents[3] / "app" / "services" / "llm_executor.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported_modules = {
        imported_module
        for imported_module in _iter_imported_modules(tree)
        if imported_module is not None
    }

    assert "litellm" in imported_modules
    assert imported_modules.isdisjoint(
        {
            "anthropic",
            "cohere",
            "google",
            "groq",
            "mistralai",
            "ollama",
            "openai",
        }
    )


def _iter_imported_modules(tree: ast.AST):
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name.split(".")[0]
        if isinstance(node, ast.ImportFrom) and node.module:
            yield node.module.split(".")[0]
