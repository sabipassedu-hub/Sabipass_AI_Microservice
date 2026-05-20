"""Layer 2 StateStrategy compiler.

Purpose: combine local complexity scoring, intent parsing, and concept
normalization into one immutable StateStrategy object. Constraints: no
downstream overrides, no RAG execution, no tutor generation, and no LLM
normalization in the Phase 3 critical path.
"""

from app.schemas.requests import NeuralChatRequest
from app.schemas.strategy import ModelStrategy, PedagogyStrategy, RagStrategy, StateStrategy
from app.services.strategy.complexity_scorer import ComplexitySignals, score_complexity
from app.services.strategy.concept_normalizer import NormalizationResult, normalize_concept
from app.services.strategy.intent_parser import IntentResult, parse_intent


PRECISION_COLLECTIONS = {
    "exam_prep": "exam_bank",
    "curriculum_coach": "curriculum_vault",
    "general_prompt": "curriculum_vault",
}


def compile_state_strategy(
    request: NeuralChatRequest,
    *,
    registry_snapshot: dict,
) -> StateStrategy:
    """Compile an immutable Layer 2 StateStrategy."""
    raw_input = request.current_interaction_context.raw_whiteboard_input
    intent = parse_intent(raw_input)
    complexity_score = score_complexity(_build_complexity_signals(request, intent))
    normalization = normalize_concept(raw_input, registry_snapshot=registry_snapshot)
    execution_path = _select_execution_path(request, complexity_score, normalization)

    return StateStrategy(
        execution_path=execution_path,
        complexity_score=complexity_score,
        normalized_concept=normalization.concept_key,
        normalization_confidence=normalization.confidence,
        normalization_status=normalization.status,
        rag_strategy=_build_rag_strategy(request, normalization),
        pedagogy_strategy=_build_pedagogy_strategy(
            request,
            intent,
            complexity_score,
            normalization,
        ),
        model_strategy=ModelStrategy(
            tier=request.student_identity.tier,
            efficiency_mode=request.efficiency_mode,
            execution_path=execution_path,
        ),
    )


def _build_complexity_signals(
    request: NeuralChatRequest,
    intent: IntentResult,
) -> ComplexitySignals:
    return ComplexitySignals(
        raw_input=request.current_interaction_context.raw_whiteboard_input,
        errors_on_same_concept_space=(
            request.current_interaction_context.errors_on_same_concept_space
        ),
        detected_frustration_signals=(
            request.emotional_telemetry.detected_frustration_signals
        ),
        rage_clicks=request.emotional_telemetry.rage_clicks,
        caps_lock_aggression=request.emotional_telemetry.caps_lock_aggression,
        sentiment_trends=request.emotional_telemetry.sentiment_trends,
        scaffolding_flag=request.cognitive_aptitude_profile.scaffolding_flag,
        complexity_tolerance=request.cognitive_aptitude_profile.complexity_tolerance,
        intent=intent.intent_type,
    )


def _select_execution_path(
    request: NeuralChatRequest,
    complexity_score: int,
    normalization: NormalizationResult,
) -> str:
    if normalization.status == "needs_clarification":
        return "single_pass"
    if request.efficiency_mode or request.student_identity.tier == "free":
        return "single_pass"
    if complexity_score >= 4:
        return "two_pass"
    return "single_pass"


def _build_rag_strategy(
    request: NeuralChatRequest,
    normalization: NormalizationResult,
) -> RagStrategy:
    if normalization.status == "needs_clarification" or normalization.concept_key is None:
        return RagStrategy(
            mode="none",
            target_collection=None,
            query_concept_key=None,
            filters=(),
            top_k=0,
        )

    if normalization.status == "degraded":
        return RagStrategy(
            mode="fallback",
            target_collection=None,
            query_concept_key=normalization.concept_key,
            filters=(),
            top_k=0,
        )

    filters = (
        ("subject", "mathematics"),
        ("topic", normalization.concept_key),
        ("exam_type", request.student_identity.exam_target),
        ("academic_stage", request.student_identity.academic_scope),
    )
    return RagStrategy(
        mode="precision",
        target_collection=PRECISION_COLLECTIONS.get(
            request.app_execution_mode,
            "curriculum_vault",
        ),
        query_concept_key=normalization.concept_key,
        filters=filters,
        top_k=3,
    )


def _build_pedagogy_strategy(
    request: NeuralChatRequest,
    intent: IntentResult,
    complexity_score: int,
    normalization: NormalizationResult,
) -> PedagogyStrategy:
    if normalization.status == "needs_clarification":
        return PedagogyStrategy(
            teaching_mode="clarification",
            response_format="micro_clarification",
            intent_type=intent.intent_type,
            urgency=intent.urgency,
        )

    return PedagogyStrategy(
        teaching_mode=_select_teaching_mode(request, intent, complexity_score),
        response_format="text_only",
        intent_type=intent.intent_type,
        urgency=intent.urgency,
    )


def _select_teaching_mode(
    request: NeuralChatRequest,
    intent: IntentResult,
    complexity_score: int,
) -> str:
    if intent.intent_type in {"answer_request", "escape_valve"}:
        return "direct_answer"
    if request.current_interaction_context.errors_on_same_concept_space >= 2:
        return "remediation"
    if intent.intent_type == "explanation" or complexity_score >= 3:
        return "direct_instruction"
    return "socratic"
