"""Per-worker runtime admission controls.

These guards are intentionally process-local. Node owns product-level rate
limits; this service prevents one Python worker from accepting more expensive
work than it can serve predictably during the demo.
"""

from contextlib import contextmanager
import threading
from typing import Iterator


class RequestAdmissionRejected(RuntimeError):
    """Raised when this worker is already serving its allowed request load."""


_RUNTIME_LOCK = threading.Lock()
_REQUEST_GUARDS_BY_LIMIT: dict[int, "WorkerAdmissionGuard"] = {}


class WorkerAdmissionGuard:
    def __init__(self, max_concurrent: int) -> None:
        if max_concurrent < 1:
            raise ValueError("max_concurrent must be at least 1")
        self.max_concurrent = max_concurrent
        self._semaphore = threading.BoundedSemaphore(max_concurrent)

    @contextmanager
    def acquire(self, *, timeout_seconds: float) -> Iterator[None]:
        acquired = self._semaphore.acquire(timeout=max(timeout_seconds, 0.0))
        if not acquired:
            raise RequestAdmissionRejected("Request capacity is exhausted in this worker")

        try:
            yield
        finally:
            self._semaphore.release()


def get_request_admission_guard(max_concurrent: int) -> WorkerAdmissionGuard:
    with _RUNTIME_LOCK:
        guard = _REQUEST_GUARDS_BY_LIMIT.get(max_concurrent)
        if guard is None:
            guard = WorkerAdmissionGuard(max_concurrent)
            _REQUEST_GUARDS_BY_LIMIT[max_concurrent] = guard
        return guard


@contextmanager
def admit_request(*, max_concurrent: int, timeout_seconds: float) -> Iterator[None]:
    guard = get_request_admission_guard(max_concurrent)
    with guard.acquire(timeout_seconds=timeout_seconds):
        yield
