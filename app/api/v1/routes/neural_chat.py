import time
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.config import get_settings
from app.db.chroma import initialize_chroma
from app.observability.metrics import emit_metric, emit_response_metrics
from app.observability.trace_buffer import append_trace_non_blocking
from app.rag.embeddings import embed_query_text
from app.registry.snapshot import get_registry_snapshot
from app.schemas.requests import NeuralChatRequest
from app.schemas.responses import SabiNeuralResponse
from app.schemas.traces import SystemTrace
from app.services.bkt_engine import calculate_student_mastery
from app.services.learning_state_adapter import (
    LearningStateControlResult,
    LearningStateValidationError,
    validate_and_normalize_learning_state,
)
from app.services.model_router import select_model_route
from app.services.rag_router import RagContext, RagRouterError, retrieve_context_for_strategy
from app.services.runtime_limits import RequestAdmissionRejected, admit_request
from app.services.strategy.compiler import compile_state_strategy
from app.services.tutor_engine import execute_tutor_response
from app.services.zero_pass import ZeroPassResult, evaluate_zero_pass


router = APIRouter()
NEURAL_CHAT_ROUTE = "/api/v1/neural/chat"


def get_chroma_collections(request: Request) -> Any:
    collections = getattr(request.app.state, "sabi_chroma_collections", None)
    return collections or initialize_chroma()


def get_embed_query(request: Request) -> Any:
    embed_query = getattr(request.app.state, "sabi_embed_query", None)
    return embed_query or embed_query_text


def get_llm_completion_callable() -> Any:
    return None


@router.post("/api/v1/neural/chat", response_model=SabiNeuralResponse)
def neural_chat(
    request: NeuralChatRequest,
    registry_snapshot: dict = Depends(get_registry_snapshot),
    collections: Any = Depends(get_chroma_collections),
    embed_query: Any = Depends(get_embed_query),
    completion_callable: Any = Depends(get_llm_completion_callable),
):
    settings = get_settings()
    started_at = time.perf_counter()
    try:
        state_control = validate_and_normalize_learning_state(
            request,
            registry_snapshot=registry_snapshot,
        )
    except LearningStateValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "invalid_learning_session_state",
                "reason": str(exc),
            },
        ) from exc

    request.learning_session_state = state_control.state
    try:
        with admit_request(
            max_concurrent=settings.request_admission_max_concurrent,
            timeout_seconds=settings.request_admission_queue_timeout_seconds,
        ):
            response = execute_neural_chat_pipeline(
                request,
                registry_snapshot=registry_snapshot,
                collections=collections,
                embed_query=embed_query,
                completion_callable=completion_callable,
                state_control=state_control,
            )
            request_status = "completed"
    except RequestAdmissionRejected:
        response = _request_admission_fallback_response(request, state_control=state_control)
        request_status = "admission_rejected"
    except Exception as exc:
        latency_ms = _elapsed_ms(started_at)
        emit_metric(
            "sabi.request.total",
            tags={
                "route": NEURAL_CHAT_ROUTE,
                "request_status": "error",
                "error_type": type(exc).__name__,
            },
        )
        emit_metric(
            "sabi.request.latency_ms",
            value=latency_ms,
            tags={
                "route": NEURAL_CHAT_ROUTE,
                "request_status": "error",
                "error_type": type(exc).__name__,
            },
        )
        raise

    _record_request_observability(
        request,
        response=response,
        request_status=request_status,
        latency_ms=_elapsed_ms(started_at),
        registry_snapshot=registry_snapshot,
    )
    return response


def execute_neural_chat_pipeline(
    request: NeuralChatRequest,
    *,
    registry_snapshot: dict,
    collections: Any = None,
    embed_query: Any = embed_query_text,
    completion_callable: Any = None,
    state_control: LearningStateControlResult | None = None,
) -> dict:
    if state_control is None:
        state_control = validate_and_normalize_learning_state(
            request,
            registry_snapshot=registry_snapshot,
        )
        request.learning_session_state = state_control.state

    zero_pass_result = evaluate_zero_pass(request)
    if zero_pass_result is not None:
        return _zero_pass_response(request, zero_pass_result, state_control=state_control)

    strategy = compile_state_strategy(
        request,
        registry_snapshot=registry_snapshot,
        state_control=state_control,
    )
    bkt_metrics = _neural_sync_payload_for_strategy(request, strategy)
    rag_context, rag_status = _retrieve_rag_context(
        strategy,
        collections=collections,
        embed_query=embed_query,
    )
    model_route, model_status = _select_model_route(strategy)
    tutor_response = execute_tutor_response(
        request=request,
        strategy=strategy,
        rag_context=rag_context,
        model_route=model_route,
        completion_callable=completion_callable,
    )
    settings = get_settings()

    return {
        "request_id": request.request_metadata.uuid_transaction_id,
        "response_type": strategy.pedagogy_strategy.response_format,
        "is_atomic": True,
        "tutor_conversational_text": tutor_response.text,
        "canvas_directive": None,
        "micro_rewards": {
            "trigger_animation": None,
            "praise_type": None,
            "xp_boost_awarded": 0,
        },
        "neural_sync_payload": bkt_metrics,
        "system_metadata": {
            "pipeline_status": "wired",
            "architecture_layer": "api_v1_neural_chat",
            "normalized_concept": strategy.normalized_concept,
            "normalization_status": strategy.normalization_status,
            "teaching_mode": strategy.pedagogy_strategy.teaching_mode,
            "rag_mode": rag_context.mode,
            "rag_status": rag_status,
            "source_tags": list(rag_context.source_tags),
            "model_status": model_status,
            "model_env_var": model_route.model_env_var if model_route else None,
            "model_name": model_route.model_name if model_route else None,
            "model_execution_path": model_route.execution_path if model_route else None,
            "llm_status": _llm_status(tutor_response),
            "llm_fallback_reason": tutor_response.fallback_reason,
            "math_verification_status": tutor_response.math_status,
            "math_verification_source": tutor_response.math_source,
            "demo_mode": settings.sabi_demo_mode,
            "demo_response_status": _demo_response_status(
                demo_mode=settings.sabi_demo_mode,
                tutor_response=tutor_response,
            ),
            "learning_state": _learning_state_metadata_for_strategy(
                state_control,
                strategy,
            ),
            "learning_engine": _learning_engine_metadata(
                strategy=strategy,
                state_control=state_control,
                bkt_metrics=bkt_metrics,
            ),
        },
    }


def _retrieve_rag_context(strategy: Any, *, collections: Any, embed_query: Any) -> tuple[RagContext, str]:
    try:
        return (
            retrieve_context_for_strategy(
                strategy,
                collections=collections,
                embed_query=embed_query,
            ),
            "completed",
        )
    except RagRouterError as exc:
        return (
            RagContext(
                mode="none",
                query_concept_key=strategy.rag_strategy.query_concept_key,
                context_text="",
                hits=(),
                source_tags=(),
            ),
            type(exc).__name__,
        )


def _select_model_route(strategy: Any):
    try:
        return (
            select_model_route(
                tier=strategy.model_strategy.tier,
                efficiency_mode=strategy.model_strategy.efficiency_mode,
                requested_execution_path=strategy.model_strategy.execution_path,
            ),
            "completed",
        )
    except RuntimeError as exc:
        return None, type(exc).__name__


def _llm_status(tutor_response: Any) -> str:
    if tutor_response.used_fallback:
        return "local_fallback"
    if tutor_response.llm_result is None:
        return "not_needed_deterministic"
    return "completed"


def _demo_response_status(*, demo_mode: bool, tutor_response: Any) -> str:
    if not demo_mode:
        return "disabled"
    if tutor_response.used_fallback:
        return "safety_fallback"
    if tutor_response.llm_result is None:
        return "deterministic_supported_prompt"
    return "live_model"


def _zero_pass_response(
    request: NeuralChatRequest,
    zero_pass_result: ZeroPassResult,
    *,
    state_control: LearningStateControlResult,
) -> dict:
    return {
        "request_id": request.request_metadata.uuid_transaction_id,
        "response_type": "zero_pass_response",
        "is_atomic": True,
        "tutor_conversational_text": zero_pass_result.tutor_text,
        "canvas_directive": None,
        "micro_rewards": zero_pass_result.micro_rewards,
        "neural_sync_payload": _safe_neural_sync_payload(request),
        "system_metadata": {
            "pipeline_status": "zero_pass_completed",
            "architecture_layer": "api_v1_neural_chat",
            "normalized_concept": zero_pass_result.concept_key,
            "normalization_status": "zero_pass",
            "teaching_mode": "zero_pass",
            "rag_mode": "none",
            "rag_status": "not_started",
            "source_tags": [],
            "model_status": "not_started",
            "model_env_var": None,
            "model_name": None,
            "model_execution_path": None,
            "llm_status": "not_needed_zero_pass",
            "llm_fallback_reason": zero_pass_result.reason,
            "math_verification_status": "not_started",
            "math_verification_source": None,
            "zero_pass_status": zero_pass_result.status,
            "zero_pass_reason": zero_pass_result.reason,
            "selected_answer": zero_pass_result.selected_answer,
            "learning_state": state_control.metadata(),
        },
    }


def _request_admission_fallback_response(
    request: NeuralChatRequest,
    *,
    state_control: LearningStateControlResult,
) -> dict:
    learning_state_metadata = dict(state_control.metadata())
    learning_state_metadata["state_mutation_allowed"] = False
    learning_state_metadata["progression_recommendation"] = "continue_current_phase"
    return {
        "request_id": request.request_metadata.uuid_transaction_id,
        "response_type": "text_only",
        "is_atomic": True,
        "tutor_conversational_text": (
            "I'm helping a lot of students right now, so let's keep this steady: "
            "send the exact step you're stuck on and I'll guide you through it one part at a time."
        ),
        "canvas_directive": None,
        "micro_rewards": {
            "trigger_animation": None,
            "praise_type": None,
            "xp_boost_awarded": 0,
        },
        "neural_sync_payload": _safe_neural_sync_payload(request),
        "system_metadata": {
            "pipeline_status": "admission_rejected",
            "architecture_layer": "api_v1_neural_chat",
            "normalized_concept": None,
            "normalization_status": "not_started",
            "teaching_mode": "fallback",
            "rag_mode": "none",
            "rag_status": "not_started",
            "source_tags": [],
            "model_status": "not_started",
            "model_env_var": None,
            "model_name": None,
            "model_execution_path": None,
            "llm_status": "local_fallback",
            "llm_fallback_reason": "request_admission_capacity_exhausted",
            "math_verification_status": "not_started",
            "math_verification_source": None,
            "learning_state": learning_state_metadata,
        },
    }


def _safe_neural_sync_payload(request: NeuralChatRequest) -> dict:
    try:
        return calculate_student_mastery(request)
    except Exception:
        return {
            "updated_bkt_mastery": 0.0,
            "calculated_learning_velocity": 0.0,
            "updated_weakness_array": [],
        }


def _neural_sync_payload_for_strategy(request: NeuralChatRequest, strategy: Any) -> dict:
    action_plan = getattr(strategy, "action_plan", None)
    if getattr(action_plan, "state_mutation_allowed", True):
        return calculate_student_mastery(request)

    learning_state = request.learning_session_state
    velocity = round(
        max(-1.0, min(1.0, float(request.cognitive_aptitude_profile.regression_slope))),
        3,
    )
    return {
        "updated_bkt_mastery": round(float(learning_state.mastery_score), 3),
        "calculated_learning_velocity": velocity,
        "updated_weakness_array": sorted(
            set(request.historical_mastery_map.active_weakness_arrays)
        ),
    }


def _learning_state_metadata_for_strategy(
    state_control: LearningStateControlResult,
    strategy: Any,
) -> dict:
    metadata = dict(state_control.metadata())
    action_plan = getattr(strategy, "action_plan", None)
    if action_plan is None:
        return metadata

    metadata.update(action_plan.metadata())
    if not action_plan.state_mutation_allowed:
        metadata["next_phase"] = metadata["phase"]
        metadata["progression_recommendation"] = "continue_current_phase"
        metadata["state_mutation_allowed"] = False
    return metadata


def _learning_engine_metadata(
    *,
    strategy: Any,
    state_control: LearningStateControlResult,
    bkt_metrics: Mapping[str, Any],
) -> dict:
    state_metadata = _learning_state_metadata_for_strategy(state_control, strategy)
    action_plan = getattr(strategy, "action_plan", None)
    action_metadata = action_plan.metadata() if action_plan is not None else {}
    return {
        "topic": state_metadata["topic"],
        "subtopic": state_metadata["subtopic"],
        "micro_skill": state_metadata["micro_skill"],
        "phase": state_metadata["phase"],
        "next_phase": state_metadata["next_phase"],
        "attempt": state_metadata["attempt"],
        "streak": state_metadata["streak"],
        "difficulty_level": state_metadata["difficulty_level"],
        "mastery_score": bkt_metrics.get("updated_bkt_mastery"),
        "progression_recommendation": state_metadata["progression_recommendation"],
        "teaching_mode": strategy.pedagogy_strategy.teaching_mode,
        "response_format": strategy.pedagogy_strategy.response_format,
        "action": action_metadata.get("action"),
        "intent": action_metadata.get("intent"),
        "intent_scores": action_metadata.get("intent_scores"),
        "intent_confidence": action_metadata.get("intent_confidence"),
        "candidate_answer": action_metadata.get("candidate_answer"),
        "state_mutation_allowed": state_metadata["state_mutation_allowed"],
        "action_reason": action_metadata.get("reason"),
        "state_effect": action_metadata.get("state_effect"),
        "anti_guessing_signal": state_metadata["anti_guessing_signal"],
        "llm_controls_progression": False,
        "frontend_controls_navigation": True,
    }


def _record_request_observability(
    request: NeuralChatRequest,
    *,
    response: Mapping[str, Any],
    request_status: str,
    latency_ms: float,
    registry_snapshot: Mapping[str, Any],
) -> None:
    metadata = response.get("system_metadata") or {}
    trace = _build_system_trace(
        request,
        response=response,
        request_status=request_status,
        latency_ms=latency_ms,
        registry_snapshot=registry_snapshot,
    )
    append_trace_non_blocking(trace)
    emit_response_metrics(
        route=NEURAL_CHAT_ROUTE,
        request_status=request_status,
        latency_ms=latency_ms,
        metadata=metadata,
    )


def _build_system_trace(
    request: NeuralChatRequest,
    *,
    response: Mapping[str, Any],
    request_status: str,
    latency_ms: float,
    registry_snapshot: Mapping[str, Any],
) -> SystemTrace:
    metadata = response.get("system_metadata") or {}
    return SystemTrace(
        request_id=str(response.get("request_id") or _request_id(request)),
        route=NEURAL_CHAT_ROUTE,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        latency_ms=latency_ms,
        request_status=request_status,
        registry_version=_optional_string(registry_snapshot.get("version")),
        student_tier=_nested_string(request, "student_identity", "tier"),
        app_execution_mode=_optional_string(getattr(request, "app_execution_mode", None)),
        response_type=_optional_string(response.get("response_type")),
        pipeline_status=_metadata_string(metadata, "pipeline_status"),
        normalized_concept=_metadata_string(metadata, "normalized_concept"),
        normalization_status=_metadata_string(metadata, "normalization_status"),
        teaching_mode=_metadata_string(metadata, "teaching_mode"),
        rag_mode=_metadata_string(metadata, "rag_mode"),
        rag_status=_metadata_string(metadata, "rag_status"),
        source_tags=[str(tag) for tag in metadata.get("source_tags") or []],
        model_status=_metadata_string(metadata, "model_status"),
        model_env_var=_metadata_string(metadata, "model_env_var"),
        model_name=_metadata_string(metadata, "model_name"),
        model_execution_path=_metadata_string(metadata, "model_execution_path"),
        llm_status=_metadata_string(metadata, "llm_status"),
        llm_fallback_reason=_metadata_string(metadata, "llm_fallback_reason"),
        math_verification_status=_metadata_string(metadata, "math_verification_status"),
        math_verification_source=_metadata_string(metadata, "math_verification_source"),
        zero_pass_status=_metadata_string(metadata, "zero_pass_status"),
        zero_pass_reason=_metadata_string(metadata, "zero_pass_reason"),
    )


def _elapsed_ms(started_at: float) -> float:
    return round((time.perf_counter() - started_at) * 1000, 3)


def _request_id(request: Any) -> str:
    metadata = getattr(request, "request_metadata", None)
    return str(getattr(metadata, "uuid_transaction_id", "unknown"))


def _nested_string(value: Any, *names: str) -> str | None:
    current = value
    for name in names:
        current = getattr(current, name, None)
        if current is None:
            return None
    return _optional_string(current)


def _metadata_string(metadata: Mapping[str, Any], key: str) -> str | None:
    return _optional_string(metadata.get(key))


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)
