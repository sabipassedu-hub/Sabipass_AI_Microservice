from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.registry.snapshot import get_registry_snapshot


router = APIRouter()
REPO_ROOT = Path(__file__).resolve().parents[4]
DEMO_SEED_PATH = REPO_ROOT / "data" / "raw" / "mock" / "waec_mathematics_mock_parse.json"


@router.get("/health")
@router.get("/api/v1/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "sabipass-ai",
    }


@router.get("/ready")
@router.get("/api/v1/ready")
def ready(request: Request) -> JSONResponse:
    settings = get_settings()
    registry_snapshot = get_registry_snapshot()
    checks: dict[str, bool] = {
        "registry": bool(registry_snapshot.get("version")),
        "demo_seed_data": (
            not settings.sabi_bootstrap_mock_data or DEMO_SEED_PATH.exists()
        ),
    }
    details: dict[str, Any] = {
        "registry_version": registry_snapshot.get("version"),
        "demo_seed_path": str(DEMO_SEED_PATH),
        "chroma_initialized": hasattr(request.app.state, "sabi_chroma_collections"),
        "trace_buffer_initialized": hasattr(request.app.state, "sabi_trace_buffer"),
    }
    is_ready = all(checks.values())
    return JSONResponse(
        status_code=200 if is_ready else 503,
        content={
            "status": "ready" if is_ready else "not_ready",
            "service": "sabipass-ai",
            "checks": checks,
            "details": details,
        },
    )
