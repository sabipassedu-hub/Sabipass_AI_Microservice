"""Layer 2 StateStrategy compiler.

Purpose: combine local complexity scoring, intent parsing, and concept
normalization into one immutable StateStrategy object. Constraints: no
downstream overrides, no RAG execution, no tutor generation, and no LLM
normalization in the Phase 3 critical path.
"""

import re

from app.schemas.requests import NeuralChatRequest
from app.schemas.strategy import ModelStrategy, PedagogyStrategy, RagStrategy, StateStrategy
from app.services.action_resolver import TutorActionPlan, resolve_tutor_action
from app.services.strategy.complexity_scorer import ComplexitySignals, score_complexity
from app.services.strategy.concept_normalizer import NormalizationResult, normalize_concept
from app.services.strategy.intent_parser import IntentResult, parse_intent


PRECISION_COLLECTIONS = {
    "exam_prep": "exam_bank",
    "curriculum_coach": "curriculum_vault",
    "homework_explainer": "curriculum_vault",
    "general_prompt": "curriculum_vault",
}
BROAD_CURRICULUM_KEYS = {
    "general_mathematics",
    "number_and_numeration",
    "algebra",
    "geometry",
    "trigonometry",
    "calculus",
}
MATH_MODES = {"exam_prep", "curriculum_coach", "homework_explainer"}
PRODUCT_NAVIGATION_SIGNALS = {
    "account",
    "billing",
    "login",
    "payment",
    "profile",
    "settings",
    "subscription",
}
TUTOR_CONTINUITY_SIGNALS = {
    "answer",
    "both sides",
    "check",
    "continue",
    "correct",
    "divide",
    "equation",
    "explain",
    "find",
    "how",
    "next",
    "practice",
    "question",
    "solve",
    "start",
    "step",
    "subtract",
    "try",
    "why",
    "wrong",
}
MATH_SYMBOL_PATTERN = re.compile(r"(?:\d+[a-z])|(?:[a-z]\s*=)|(?:[+\-*/=])")


def compile_state_strategy(
    request: NeuralChatRequest,
    *,
    registry_snapshot: dict,
    state_control: object | None = None,
) -> StateStrategy:
    """Compile an immutable Layer 2 StateStrategy."""
    raw_input = request.current_interaction_context.raw_whiteboard_input
    intent = parse_intent(
        raw_input,
        session_state=request.learning_session_state,
        current_interaction_context=request.current_interaction_context,
    )
    action_plan = resolve_tutor_action(
        intent=intent,
        learning_state=request.learning_session_state,
    )
    complexity_score = score_complexity(_build_complexity_signals(request, intent))
    normalization = _resolve_concept_with_state_continuity(
        request,
        normalize_concept(raw_input, registry_snapshot=registry_snapshot),
        registry_snapshot=registry_snapshot,
        intent=intent,
    )
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
            action_plan,
            complexity_score,
            normalization,
        ),
        model_strategy=ModelStrategy(
            tier=request.student_identity.tier,
            efficiency_mode=request.efficiency_mode,
            execution_path=execution_path,
        ),
        learning_state=request.learning_session_state,
        state_control=(
            state_control.metadata()
            if hasattr(state_control, "metadata")
            else None
        ),
        action_plan=action_plan,
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


def _resolve_concept_with_state_continuity(
    request: NeuralChatRequest,
    normalization: NormalizationResult,
    *,
    registry_snapshot: dict,
    intent: IntentResult,
) -> NormalizationResult:
    """Use restored learning state as the topic anchor for valid math follow-ups."""
    if normalization.status in {"strict", "semantic"}:
        return normalization

    canonical_keys = registry_snapshot.get("canonical_keys") or {}
    state_concept = _learning_state_concept_key(request, canonical_keys)
    if state_concept is None:
        return normalization

    raw_input = request.current_interaction_context.raw_whiteboard_input
    if not _is_tutoring_continuation(request, raw_input, intent):
        return normalization

    return NormalizationResult(
        concept_key=state_concept,
        confidence=0.88,
        status="strict",
        matched_text="learning_session_state",
    )


def _learning_state_concept_key(
    request: NeuralChatRequest,
    canonical_keys: dict[str, dict],
) -> str | None:
    state = getattr(request, "learning_session_state", None)
    if state is None:
        return None

    topic = getattr(state, "topic", None)
    subtopic = getattr(state, "subtopic", None)
    micro_skill = getattr(state, "micro_skill", None)

    for candidate in (topic, subtopic, micro_skill):
        if candidate and candidate not in canonical_keys:
            return None

    if topic and topic not in BROAD_CURRICULUM_KEYS:
        return topic
    if subtopic:
        parent_key = canonical_keys.get(subtopic, {}).get("parent_key")
        if parent_key == topic and subtopic in BROAD_CURRICULUM_KEYS and micro_skill:
            return micro_skill
        return subtopic
    return topic


def _is_tutoring_continuation(
    request: NeuralChatRequest,
    raw_input: str,
    intent: IntentResult,
) -> bool:
    normalized = " ".join(raw_input.lower().split())
    tokens = set(normalized.replace("_", " ").split())

    if tokens & PRODUCT_NAVIGATION_SIGNALS and not _has_math_signal(normalized, tokens):
        return False

    if request.app_execution_mode in MATH_MODES:
        phase = getattr(request.learning_session_state, "phase", None)
        return (
            phase in {"explanation", "guided_example"}
            or intent.intent_type in {"explanation", "evaluation"}
            or (intent.intent_type == "confusion" and bool(intent.matched_signals))
            or _has_math_signal(normalized, tokens)
        )

    if intent.intent_type in {"explanation", "evaluation"}:
        return True
    if intent.intent_type == "confusion" and intent.matched_signals:
        return True

    return _has_math_signal(normalized, tokens)


def _has_math_signal(normalized: str, tokens: set[str]) -> bool:
    if tokens & TUTOR_CONTINUITY_SIGNALS:
        return True
    return MATH_SYMBOL_PATTERN.search(normalized) is not None


def _build_pedagogy_strategy(
    request: NeuralChatRequest,
    intent: IntentResult,
    action_plan: TutorActionPlan,
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
        teaching_mode=_select_teaching_mode(request, intent, action_plan, complexity_score),
        response_format="text_only",
        intent_type=intent.intent_type,
        urgency=intent.urgency,
    )


def _select_teaching_mode(
    request: NeuralChatRequest,
    intent: IntentResult,
    action_plan: TutorActionPlan,
    complexity_score: int,
) -> str:
    if action_plan.action_type == "explain_step":
        return "direct_instruction"
    if action_plan.action_type == "guided_example":
        return "guided_example"
    if action_plan.action_type == "give_practice":
        return "practice"
    if action_plan.action_type == "grade_answer":
        return "evaluation"
    if action_plan.action_type == "give_hint":
        return "remediation"
    if action_plan.action_type == "intervention":
        return "system_intervention"
    if request.current_interaction_context.errors_on_same_concept_space >= 2:
        return "remediation"
    if intent.intent_type == "explanation" or complexity_score >= 3:
        return "direct_instruction"
    return "socratic"
