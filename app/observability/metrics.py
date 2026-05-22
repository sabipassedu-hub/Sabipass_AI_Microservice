"""Layer 8 metrics emission."""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from typing import Any


LOGGER = logging.getLogger("sabipass.metrics")


def emit_metric(
    name: str,
    *,
    value: float = 1.0,
    tags: Mapping[str, Any] | None = None,
) -> bool:
    """Emit one structured metric event without raising to request handlers."""
    try:
        payload = {
            "metric": name,
            "value": value,
            "tags": _stringify_tags(tags or {}),
        }
        LOGGER.info(
            json.dumps(payload, separators=(",", ":"), sort_keys=True),
            extra={"sabi_metric": payload},
        )
    except Exception:
        return False
    return True


def emit_response_metrics(
    *,
    route: str,
    request_status: str,
    latency_ms: float,
    metadata: Mapping[str, Any],
) -> None:
    """Emit the low-cardinality request metrics used by demo operations."""
    base_tags = {
        "route": route,
        "request_status": request_status,
        "pipeline_status": metadata.get("pipeline_status") or "unknown",
    }
    emit_metric("sabi.request.total", tags=base_tags)
    emit_metric("sabi.request.latency_ms", value=latency_ms, tags=base_tags)
    emit_metric(
        "sabi.rag.status",
        tags={
            **base_tags,
            "rag_status": metadata.get("rag_status") or "unknown",
            "rag_mode": metadata.get("rag_mode") or "unknown",
        },
    )
    emit_metric(
        "sabi.model.status",
        tags={
            **base_tags,
            "model_status": metadata.get("model_status") or "unknown",
            "llm_status": metadata.get("llm_status") or "unknown",
            "model_execution_path": metadata.get("model_execution_path") or "none",
        },
    )
    emit_metric(
        "sabi.math.status",
        tags={
            **base_tags,
            "math_verification_status": (
                metadata.get("math_verification_status") or "unknown"
            ),
            "math_verification_source": (
                metadata.get("math_verification_source") or "unknown"
            ),
        },
    )

    fallback_reason = metadata.get("llm_fallback_reason")
    if fallback_reason:
        emit_metric(
            "sabi.fallback.reason",
            tags={**base_tags, "fallback_reason": fallback_reason},
        )


def _stringify_tags(tags: Mapping[str, Any]) -> dict[str, str]:
    return {
        str(key): "none" if value is None else str(value)
        for key, value in tags.items()
    }
