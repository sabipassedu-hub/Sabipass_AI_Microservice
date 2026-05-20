"""Layer 6 LiteLLM executor.

Purpose: centralize all LLM calls through LiteLLM so the service remains
provider-agnostic. Constraints: this module must never import provider SDKs
directly, must receive routing decisions from `model_router`, and must execute
strategy rather than reinterpreting pedagogy, RAG, or math decisions.
"""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from app.services.model_router import ExecutionPath, ModelRoute, ProviderInterface


Message = Mapping[str, str]
CompletionCallable = Callable[..., Any]


@dataclass(frozen=True)
class LLMExecutionRequest:
    """Minimal executable prompt packet for one LiteLLM call."""

    route: ModelRoute
    messages: Sequence[Message]
    temperature: float = 0.2
    max_tokens: int = 700

    def __post_init__(self) -> None:
        if not self.messages:
            raise ValueError("messages must contain at least one message")
        if self.temperature < 0:
            raise ValueError("temperature must be non-negative")
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")


@dataclass(frozen=True)
class LLMExecutionResult:
    """Normalized text output from a LiteLLM response."""

    text: str
    model: str
    provider_interface: ProviderInterface
    execution_path: ExecutionPath


def execute_llm_call(
    request: LLMExecutionRequest,
    *,
    completion_callable: CompletionCallable | None = None,
) -> LLMExecutionResult:
    """Execute one model call through a LiteLLM-compatible completion function."""
    if request.route.provider_interface != "litellm":
        raise ValueError("LLM execution must use the LiteLLM provider interface")

    completion = completion_callable or _call_litellm_completion
    response = completion(
        model=request.route.model_name,
        messages=[dict(message) for message in request.messages],
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )

    return LLMExecutionResult(
        text=_extract_response_text(response),
        model=request.route.model_name,
        provider_interface=request.route.provider_interface,
        execution_path=request.route.execution_path,
    )


def _call_litellm_completion(**kwargs: Any) -> Any:
    from litellm import completion

    return completion(**kwargs)


def _extract_response_text(response: Any) -> str:
    choices = _get_value(response, "choices")
    if not choices:
        raise ValueError("LiteLLM response did not include choices")

    first_choice = choices[0]
    message = _get_value(first_choice, "message")
    content = _get_value(message, "content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("LiteLLM response did not include message content")

    return content


def _get_value(value: Any, key: str) -> Any:
    if isinstance(value, Mapping):
        return value.get(key)
    return getattr(value, key, None)
