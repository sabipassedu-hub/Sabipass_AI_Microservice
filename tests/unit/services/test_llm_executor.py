import ast
from pathlib import Path
import time
from types import SimpleNamespace

import pytest

from app.services import llm_executor
from app.services.llm_executor import (
    LLMExecutionRequest,
    LLMExecutionResult,
    ModelCapacityError,
    ModelCircuitOpenError,
    ModelTimeoutError,
    execute_llm_call,
)
from app.services.model_router import ModelRoute


@pytest.fixture(autouse=True)
def reset_llm_circuit():
    llm_executor._CIRCUIT_BREAKER = None
    yield
    llm_executor._CIRCUIT_BREAKER = None


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
        "timeout": 2.5,
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


def test_llm_executor_times_out_slow_provider(monkeypatch):
    monkeypatch.setattr(
        llm_executor,
        "get_settings",
        lambda: _settings(
            llm_timeout_seconds=0.01,
            llm_max_concurrent_requests=1,
            llm_circuit_failure_threshold=10,
        ),
    )
    request = LLMExecutionRequest(
        route=model_route(),
        messages=({"role": "user", "content": "Solve 2x = 6"},),
    )

    def slow_completion(**kwargs):
        time.sleep(0.2)
        return {"choices": [{"message": {"content": "Too late"}}]}

    with pytest.raises(ModelTimeoutError):
        execute_llm_call(request, completion_callable=slow_completion)


def test_llm_executor_rejects_when_local_capacity_is_exhausted(monkeypatch):
    monkeypatch.setattr(
        llm_executor,
        "get_settings",
        lambda: _settings(
            llm_timeout_seconds=0.5,
            llm_queue_timeout_seconds=0.001,
            llm_max_concurrent_requests=1,
            llm_circuit_failure_threshold=10,
        ),
    )
    semaphore = llm_executor._get_semaphore(1)
    assert semaphore.acquire(timeout=0.001)
    request = LLMExecutionRequest(
        route=model_route(),
        messages=({"role": "user", "content": "Solve 2x = 6"},),
    )
    try:
        with pytest.raises(ModelCapacityError):
            execute_llm_call(
                request,
                completion_callable=lambda **_: {
                    "choices": [{"message": {"content": "Should not run"}}]
                },
            )
    finally:
        semaphore.release()


def test_llm_executor_opens_circuit_after_repeated_provider_failures(monkeypatch):
    monkeypatch.setattr(
        llm_executor,
        "get_settings",
        lambda: _settings(
            llm_timeout_seconds=0.1,
            llm_max_concurrent_requests=2,
            llm_circuit_failure_threshold=1,
            llm_circuit_reset_seconds=60.0,
        ),
    )
    request = LLMExecutionRequest(
        route=model_route(),
        messages=({"role": "user", "content": "Solve 2x = 6"},),
    )

    with pytest.raises(llm_executor.ModelProviderError):
        execute_llm_call(
            request,
            completion_callable=lambda **_: (_ for _ in ()).throw(RuntimeError("boom")),
        )

    with pytest.raises(ModelCircuitOpenError):
        execute_llm_call(
            request,
            completion_callable=lambda **_: {
                "choices": [{"message": {"content": "Should not run"}}]
            },
        )


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


def _settings(**overrides):
    defaults = {
        "llm_timeout_seconds": 2.5,
        "llm_queue_timeout_seconds": 0.05,
        "llm_max_concurrent_requests": 4,
        "llm_retry_attempts": 1,
        "llm_retry_min_seconds": 0.05,
        "llm_retry_max_seconds": 0.2,
        "llm_circuit_failure_threshold": 5,
        "llm_circuit_reset_seconds": 20.0,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)
