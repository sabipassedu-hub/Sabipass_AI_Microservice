"""Layer 8 trace flush worker."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from app.observability.trace_buffer import TraceBuffer, get_trace_buffer
from app.schemas.traces import SystemTrace


DEFAULT_TRACE_LOG_PATH = Path("logs") / "sabipass_traces.jsonl"
LOGGER = logging.getLogger("sabipass.observability.traces")


async def flush_trace_batch(
    buffer: TraceBuffer | None = None,
    *,
    log_path: str | Path = DEFAULT_TRACE_LOG_PATH,
    batch_size: int = 100,
) -> int:
    """Flush a bounded batch of buffered traces to JSONL."""
    active_buffer = buffer or get_trace_buffer()
    traces = active_buffer.drain(batch_size)
    if not traces:
        return 0

    try:
        await asyncio.to_thread(_append_jsonl, Path(log_path), traces)
    except Exception:
        active_buffer.prepend_many(traces)
        LOGGER.exception("Failed to flush SabiPass request traces")
        return 0

    return len(traces)


async def run_trace_flush_worker(
    buffer: TraceBuffer,
    *,
    log_path: str | Path = DEFAULT_TRACE_LOG_PATH,
    interval_seconds: float = 1.0,
    batch_size: int = 100,
) -> None:
    """Continuously drain traces until the lifespan task is cancelled."""
    try:
        while True:
            await flush_trace_batch(
                buffer,
                log_path=log_path,
                batch_size=batch_size,
            )
            await asyncio.sleep(interval_seconds)
    except asyncio.CancelledError:
        await flush_trace_batch(buffer, log_path=log_path, batch_size=batch_size)
        raise


def start_trace_flush_worker(
    buffer: TraceBuffer,
    *,
    log_path: str | Path = DEFAULT_TRACE_LOG_PATH,
    interval_seconds: float = 1.0,
    batch_size: int = 100,
) -> asyncio.Task[None]:
    """Start the lifespan-managed trace flush task."""
    return asyncio.create_task(
        run_trace_flush_worker(
            buffer,
            log_path=log_path,
            interval_seconds=interval_seconds,
            batch_size=batch_size,
        )
    )


def _append_jsonl(path: Path, traces: list[SystemTrace]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(
            trace.model_dump(mode="json"),
            separators=(",", ":"),
            sort_keys=True,
        )
        for trace in traces
    ]
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
        handle.write("\n")
