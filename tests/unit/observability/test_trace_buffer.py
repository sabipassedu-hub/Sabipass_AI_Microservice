import asyncio
import json
from pathlib import Path

from app.observability.flush_worker import flush_trace_batch
from app.observability.trace_buffer import TraceBuffer
from app.schemas.traces import SystemTrace


def test_trace_buffer_is_bounded_and_drains_fifo():
    buffer = TraceBuffer(maxlen=2)

    buffer.append(_trace("trace-1"))
    buffer.append(_trace("trace-2"))
    buffer.append(_trace("trace-3"))

    assert buffer.dropped_count == 1
    assert [trace.request_id for trace in buffer.drain(10)] == ["trace-2", "trace-3"]
    assert len(buffer) == 0


def test_flush_trace_batch_writes_jsonl_without_request_path_disk_io(tmp_path: Path):
    buffer = TraceBuffer(maxlen=3)
    buffer.append(_trace("trace-jsonl"))
    log_path = tmp_path / "traces.jsonl"

    flushed = asyncio.run(
        flush_trace_batch(buffer, log_path=log_path, batch_size=10)
    )

    assert flushed == 1
    payload = json.loads(log_path.read_text(encoding="utf-8").strip())
    assert payload["request_id"] == "trace-jsonl"
    assert payload["trace_version"] == "phase6.v1"
    assert len(buffer) == 0


def _trace(request_id: str) -> SystemTrace:
    return SystemTrace(
        request_id=request_id,
        route="/api/v1/neural/chat",
        timestamp_utc="2026-05-21T12:00:00+00:00",
        latency_ms=1.5,
        request_status="completed",
        registry_version="1.0",
        rag_status="not_started",
        model_status="not_started",
        llm_status="not_needed_zero_pass",
        math_verification_status="not_started",
    )
