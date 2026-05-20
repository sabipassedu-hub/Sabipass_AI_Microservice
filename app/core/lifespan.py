"""FastAPI lifespan registration for background workers.

Layer 8 observability workers and Layer 11 polling hooks must be registered
through FastAPI lifespan contexts instead of deprecated startup events.
Constraints: startup must not run blocking work, request handlers must not
perform disk I/O for traces, and unfinished workers must shut down cleanly.
The current lifespan is intentionally no-op until those workers are built.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from pipelines.ingestion.chroma_seed import seed_demo_collections


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    app.state.sabi_settings = settings
    if settings.sabi_bootstrap_mock_data:
        seed_demo_collections()
    yield


def start_lifespan_workers() -> None:
    """Start registered background workers when Layer 8 is implemented."""
    raise NotImplementedError("FastAPI lifespan workers are not implemented yet.")
