"""Layer 8 trace flush worker.

Purpose: batch-pop traces from the in-memory buffer and append JSONL outside
the request lifecycle. Constraints: registered by FastAPI lifespan, crash
behavior must be observable, and request handlers must not await disk writes.
"""


async def flush_trace_batch() -> None:
    """Flush a batch of buffered traces."""
    raise NotImplementedError("Layer 8 trace flushing is not implemented yet.")
