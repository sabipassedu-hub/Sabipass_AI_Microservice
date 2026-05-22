"""Layer 6 LiteLLM executor.

Purpose: centralize all LLM calls through LiteLLM so the service remains
provider-agnostic. Constraints: this module must never import provider SDKs
directly, must receive routing decisions from `model_router`, and must execute
strategy rather than reinterpreting pedagogy, RAG, or math decisions.
"""

from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import dataclass
import threading
import time
from typing import Any

from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.services.model_router import ExecutionPath, ModelRoute, ProviderInterface


Message = Mapping[str, str]
CompletionCallable = Callable[..., Any]


class LLMExecutionError(RuntimeError):
    """Base error for bounded model execution failures."""


class ModelCapacityError(LLMExecutionError):
    """Raised when this worker is already serving its allowed model calls."""


class ModelCircuitOpenError(LLMExecutionError):
    """Raised when recent provider failures should short-circuit new calls."""


class ModelProviderError(LLMExecutionError):
    """Raised when the provider call fails before a usable response is returned."""


class ModelTimeoutError(LLMExecutionError):
    """Raised when a provider call exceeds the configured hard timeout."""


_RUNTIME_LOCK = threading.Lock()
_SEMAPHORE_BY_LIMIT: dict[int, threading.BoundedSemaphore] = {}
_EXECUTOR_BY_LIMIT: dict[int, ThreadPoolExecutor] = {}
_CIRCUIT_BREAKER = None


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

    settings = get_settings()
    circuit_breaker = _get_circuit_breaker(
        failure_threshold=settings.llm_circuit_failure_threshold,
        reset_seconds=settings.llm_circuit_reset_seconds,
    )
    circuit_breaker.raise_if_open()

    semaphore = _get_semaphore(settings.llm_max_concurrent_requests)
    acquired = semaphore.acquire(timeout=settings.llm_queue_timeout_seconds)
    if not acquired:
        raise ModelCapacityError("LLM capacity is exhausted in this worker")

    try:
        completion = completion_callable or _get_litellm_completion()
    except Exception as exc:
        circuit_breaker.record_failure()
        raise ModelProviderError(type(exc).__name__) from exc

    call_kwargs = {
        "model": request.route.model_name,
        "messages": [dict(message) for message in request.messages],
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
        "timeout": settings.llm_timeout_seconds,
    }

    try:
        response = _execute_with_retry(
            completion,
            call_kwargs,
            max_workers=settings.llm_max_concurrent_requests,
            timeout_seconds=settings.llm_timeout_seconds,
            attempts=settings.llm_retry_attempts,
            retry_min_seconds=settings.llm_retry_min_seconds,
            retry_max_seconds=settings.llm_retry_max_seconds,
        )
        result = LLMExecutionResult(
            text=_extract_response_text(response),
            model=request.route.model_name,
            provider_interface=request.route.provider_interface,
            execution_path=request.route.execution_path,
        )
    except (ModelProviderError, ModelTimeoutError):
        circuit_breaker.record_failure()
        raise
    except Exception as exc:
        circuit_breaker.record_failure()
        raise ModelProviderError(type(exc).__name__) from exc
    finally:
        semaphore.release()

    circuit_breaker.record_success()
    return result


def _get_litellm_completion() -> CompletionCallable:
    from litellm import completion

    return completion


def _execute_with_retry(
    completion: CompletionCallable,
    call_kwargs: dict[str, Any],
    *,
    max_workers: int,
    timeout_seconds: float,
    attempts: int,
    retry_min_seconds: float,
    retry_max_seconds: float,
) -> Any:
    retryer = Retrying(
        reraise=True,
        stop=stop_after_attempt(attempts),
        wait=wait_exponential(
            multiplier=max(retry_min_seconds, 0.001),
            min=retry_min_seconds,
            max=max(retry_max_seconds, retry_min_seconds),
        ),
        retry=retry_if_exception_type(ModelProviderError),
    )

    return retryer(
        _execute_completion_once,
        completion,
        call_kwargs,
        max_workers=max_workers,
        timeout_seconds=timeout_seconds,
    )


def _execute_completion_once(
    completion: CompletionCallable,
    call_kwargs: dict[str, Any],
    *,
    max_workers: int,
    timeout_seconds: float,
) -> Any:
    executor = _get_executor(max_workers)
    future = executor.submit(completion, **call_kwargs)
    try:
        return future.result(timeout=timeout_seconds)
    except FutureTimeoutError as exc:
        future.cancel()
        raise ModelTimeoutError("LLM provider call timed out") from exc
    except Exception as exc:
        raise ModelProviderError(type(exc).__name__) from exc


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


def _get_semaphore(max_concurrent: int) -> threading.BoundedSemaphore:
    with _RUNTIME_LOCK:
        semaphore = _SEMAPHORE_BY_LIMIT.get(max_concurrent)
        if semaphore is None:
            semaphore = threading.BoundedSemaphore(max_concurrent)
            _SEMAPHORE_BY_LIMIT[max_concurrent] = semaphore
        return semaphore


def _get_executor(max_workers: int) -> ThreadPoolExecutor:
    with _RUNTIME_LOCK:
        executor = _EXECUTOR_BY_LIMIT.get(max_workers)
        if executor is None:
            executor = ThreadPoolExecutor(
                max_workers=max_workers,
                thread_name_prefix="sabi-llm",
            )
            _EXECUTOR_BY_LIMIT[max_workers] = executor
        return executor


def _get_circuit_breaker(*, failure_threshold: int, reset_seconds: float):
    global _CIRCUIT_BREAKER
    with _RUNTIME_LOCK:
        if (
            _CIRCUIT_BREAKER is None
            or _CIRCUIT_BREAKER.failure_threshold != failure_threshold
            or _CIRCUIT_BREAKER.reset_seconds != reset_seconds
        ):
            _CIRCUIT_BREAKER = _ModelCircuitBreaker(
                failure_threshold=failure_threshold,
                reset_seconds=reset_seconds,
            )
        return _CIRCUIT_BREAKER


class _ModelCircuitBreaker:
    def __init__(self, *, failure_threshold: int, reset_seconds: float) -> None:
        self.failure_threshold = failure_threshold
        self.reset_seconds = reset_seconds
        self._failure_count = 0
        self._opened_at: float | None = None
        self._lock = threading.Lock()

    def raise_if_open(self) -> None:
        with self._lock:
            if self._opened_at is None:
                return
            if time.monotonic() - self._opened_at >= self.reset_seconds:
                self._opened_at = None
                self._failure_count = 0
                return
            raise ModelCircuitOpenError("LLM circuit is temporarily open")

    def record_success(self) -> None:
        with self._lock:
            self._failure_count = 0
            self._opened_at = None

    def record_failure(self) -> None:
        with self._lock:
            self._failure_count += 1
            if self._failure_count >= self.failure_threshold:
                self._opened_at = time.monotonic()
