"""Layer 8 SystemTrace schema."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


RequestTraceStatus = Literal["completed", "admission_rejected", "error"]


class SystemTrace(BaseModel):
    """Request trace persisted outside the student-facing response."""

    trace_version: str = "phase6.v1"
    request_id: str
    route: str
    timestamp_utc: str
    latency_ms: float = Field(ge=0)
    request_status: RequestTraceStatus
    registry_version: str | None = None
    student_tier: str | None = None
    app_execution_mode: str | None = None
    response_type: str | None = None
    pipeline_status: str | None = None
    normalized_concept: str | None = None
    normalization_status: str | None = None
    teaching_mode: str | None = None
    rag_mode: str | None = None
    rag_status: str | None = None
    source_tags: list[str] = Field(default_factory=list)
    model_status: str | None = None
    model_env_var: str | None = None
    model_name: str | None = None
    model_execution_path: str | None = None
    llm_status: str | None = None
    llm_fallback_reason: str | None = None
    math_verification_status: str | None = None
    math_verification_source: str | None = None
    zero_pass_status: str | None = None
    zero_pass_reason: str | None = None
