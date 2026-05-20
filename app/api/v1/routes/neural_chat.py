from typing import Any

from fastapi import APIRouter, Depends

from app.db.chroma import initialize_chroma
from app.rag.embeddings import embed_query_text
from app.registry.snapshot import get_registry_snapshot
from app.schemas.requests import NeuralChatRequest
from app.schemas.responses import SabiNeuralResponse
from app.services.bkt_engine import calculate_student_mastery
from app.services.model_router import select_model_route
from app.services.rag_router import RagContext, RagRouterError, retrieve_context_for_strategy
from app.services.strategy.compiler import compile_state_strategy
from app.services.tutor_engine import execute_tutor_response


router = APIRouter()


def get_chroma_collections() -> Any:
    return initialize_chroma()


def get_embed_query() -> Any:
    return embed_query_text


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
    return execute_neural_chat_pipeline(
        request,
        registry_snapshot=registry_snapshot,
        collections=collections,
        embed_query=embed_query,
        completion_callable=completion_callable,
    )


def execute_neural_chat_pipeline(
    request: NeuralChatRequest,
    *,
    registry_snapshot: dict,
    collections: Any = None,
    embed_query: Any = embed_query_text,
    completion_callable: Any = None,
) -> dict:
    bkt_metrics = calculate_student_mastery(request)
    strategy = compile_state_strategy(request, registry_snapshot=registry_snapshot)
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
            "model_execution_path": model_route.execution_path if model_route else None,
            "llm_status": _llm_status(tutor_response),
            "llm_fallback_reason": tutor_response.fallback_reason,
            "math_verification_status": tutor_response.math_status,
            "math_verification_source": tutor_response.math_source,
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
        return "not_needed_verified_math"
    return "completed"
