"""Layer 8 bounded trace buffer."""

from __future__ import annotations

from collections import deque
from threading import Lock

from app.schemas.traces import SystemTrace


DEFAULT_TRACE_BUFFER_SIZE = 1_000


class TraceBuffer:
    """Thread-safe bounded FIFO buffer for request traces."""

    def __init__(self, maxlen: int = DEFAULT_TRACE_BUFFER_SIZE) -> None:
        if maxlen < 1:
            raise ValueError("TraceBuffer maxlen must be at least 1")
        self.maxlen = maxlen
        self._items: deque[SystemTrace] = deque(maxlen=maxlen)
        self._lock = Lock()
        self._dropped_count = 0

    @property
    def dropped_count(self) -> int:
        with self._lock:
            return self._dropped_count

    def append(self, trace: SystemTrace) -> bool:
        """Append one trace and drop the oldest when the buffer is full."""
        with self._lock:
            if len(self._items) == self.maxlen:
                self._dropped_count += 1
            self._items.append(trace)
        return True

    def drain(self, max_items: int) -> list[SystemTrace]:
        """Remove and return up to ``max_items`` traces in FIFO order."""
        if max_items < 1:
            return []

        drained: list[SystemTrace] = []
        with self._lock:
            while self._items and len(drained) < max_items:
                drained.append(self._items.popleft())
        return drained

    def prepend_many(self, traces: list[SystemTrace]) -> None:
        """Restore traces after a failed flush, preserving original order."""
        if not traces:
            return

        with self._lock:
            for trace in reversed(traces):
                if len(self._items) == self.maxlen:
                    self._items.pop()
                    self._dropped_count += 1
                self._items.appendleft(trace)

    def snapshot(self) -> list[SystemTrace]:
        with self._lock:
            return list(self._items)

    def __len__(self) -> int:
        with self._lock:
            return len(self._items)


_DEFAULT_TRACE_BUFFER = TraceBuffer()


def configure_trace_buffer(maxlen: int) -> TraceBuffer:
    """Replace the process-local buffer during application startup."""
    global _DEFAULT_TRACE_BUFFER
    _DEFAULT_TRACE_BUFFER = TraceBuffer(maxlen=maxlen)
    return _DEFAULT_TRACE_BUFFER


def get_trace_buffer() -> TraceBuffer:
    return _DEFAULT_TRACE_BUFFER


def append_trace_non_blocking(trace: SystemTrace, buffer: TraceBuffer | None = None) -> bool:
    """Best-effort request-path append that never raises to callers."""
    try:
        (buffer or get_trace_buffer()).append(trace)
    except Exception:
        return False
    return True
