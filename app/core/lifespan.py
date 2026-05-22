"""FastAPI lifespan registration for background workers.

Layer 8 observability workers and Layer 11 polling hooks must be registered
through FastAPI lifespan contexts instead of deprecated startup events.
Constraints: startup must not run blocking work, request handlers must not
perform disk I/O for traces, and unfinished workers must shut down cleanly.
The current lifespan is intentionally no-op until those workers are built.
"""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI

from app.core.config import get_settings
from app.db.chroma import initialize_chroma
from app.observability.flush_worker import flush_trace_batch, start_trace_flush_worker
from app.observability.trace_buffer import configure_trace_buffer
from app.rag.embeddings import embed_query_text, warm_embedding_model
from pipelines.ingestion.chroma_seed import seed_demo_collections


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    trace_buffer = configure_trace_buffer(
        getattr(settings, "observability_trace_buffer_size", 1000)
    )
    trace_flush_task: asyncio.Task[None] | None = None
    app.state.sabi_settings = settings
    app.state.sabi_trace_buffer = trace_buffer
    app.state.sabi_chroma_collections = initialize_chroma()
    app.state.sabi_embed_query = embed_query_text
    app.state.sabi_embedding_model_name = None
    app.state.sabi_demo_seed_result = None

    if getattr(settings, "observability_trace_flush_enabled", True):
        trace_flush_task = start_trace_flush_worker(
            trace_buffer,
            log_path=getattr(
                settings,
                "observability_trace_log_path",
                "logs/sabipass_traces.jsonl",
            ),
            interval_seconds=getattr(
                settings,
                "observability_trace_flush_interval_seconds",
                1.0,
            ),
            batch_size=getattr(settings, "observability_trace_flush_batch_size", 100),
        )

    if settings.sabi_bootstrap_mock_data:
        app.state.sabi_embedding_model_name = warm_embedding_model()
        app.state.sabi_demo_seed_result = seed_demo_collections()
    try:
        yield
    finally:
        if trace_flush_task is not None:
            trace_flush_task.cancel()
            with suppress(asyncio.CancelledError):
                await trace_flush_task
        await flush_trace_batch(
            trace_buffer,
            log_path=getattr(
                settings,
                "observability_trace_log_path",
                "logs/sabipass_traces.jsonl",
            ),
            batch_size=getattr(settings, "observability_trace_flush_batch_size", 100),
        )


def start_lifespan_workers() -> None:
    """Compatibility hook; workers are managed by the FastAPI lifespan."""
    return None
