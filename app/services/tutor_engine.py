"""Layer 5/6 tutor orchestration for strategy-bound response generation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from app.services.llm_executor import (
    CompletionCallable,
    LLMExecutionRequest,
    LLMExecutionResult,
    execute_llm_call,
)
from app.services.math_verifier import MathVerificationResult, verify_math_request
from app.services.model_router import ModelRoute


PIDGIN_SIGNALS = {
    "abeg",
    "dey",
    "dem",
    "how i go",
    "no wahala",
    "sha",
    "wey",
    "wetin",
}


@dataclass(frozen=True)
class TutorResponseResult:
    text: str
    llm_result: LLMExecutionResult | None
    used_fallback: bool
    fallback_reason: str | None = None
    math_status: str = "unsupported"
    math_source: str = "none"


def execute_tutor_response(
    *,
    request: Any,
    strategy: Any,
    rag_context: Any,
    model_route: ModelRoute | None,
    completion_callable: CompletionCallable | None = None,
) -> TutorResponseResult:
    """Execute the compiled strategy through the approved LLM path."""
    if model_route is None:
        return _fallback_result(request, strategy, rag_context, "model_route_unavailable")

    if strategy.pedagogy_strategy.response_format == "micro_clarification":
        return _fallback_result(request, strategy, rag_context, "clarification_required")

    math_result = verify_math_request(
        request.current_interaction_context.raw_whiteboard_input,
        concept_key=strategy.normalized_concept,
    )
    if math_result.response_text is not None and completion_callable is None:
        return TutorResponseResult(
            text=math_result.response_text,
            llm_result=None,
            used_fallback=False,
            math_status=math_result.status,
            math_source=math_result.source,
        )

    messages = build_tutor_messages(request, strategy, rag_context, math_result=math_result)
    try:
        llm_result = execute_llm_call(
            LLMExecutionRequest(
                route=model_route,
                messages=messages,
                temperature=0.2,
                max_tokens=700,
            ),
            completion_callable=completion_callable,
        )
    except Exception as exc:
        return _fallback_result(request, strategy, rag_context, type(exc).__name__)

    return TutorResponseResult(
        text=llm_result.text,
        llm_result=llm_result,
        used_fallback=False,
        math_status=math_result.status,
        math_source=math_result.source,
    )


def build_tutor_messages(
    request: Any,
    strategy: Any,
    rag_context: Any,
    *,
    math_result: MathVerificationResult | None = None,
) -> tuple[Mapping[str, str], ...]:
    """Build a prompt packet where the LLM executes, not chooses, strategy."""
    raw_input = request.current_interaction_context.raw_whiteboard_input
    language_guidance = (
        "Use simple Nigerian Pidgin-flavoured English because the student used Pidgin."
        if _looks_like_pidgin(raw_input)
        else "Use clear, simple English."
    )
    context_text = rag_context.context_text.strip() or "No verified retrieval context was found."
    math_context = (
        math_result.prompt_context
        if math_result is not None
        else "No deterministic math verification was available."
    )

    system_message = (
        "You are SabiPass, a WAEC and JAMB mathematics tutor. "
        "Execute the supplied strategy only. Do not invent exam facts. "
        "Teach the reliable next step before giving any final answer. "
        "When math_grounding is provided, do not contradict it."
    )
    user_message = "\n".join(
        [
            f"student_input={raw_input}",
            f"exam_target={request.student_identity.exam_target}",
            f"academic_scope={request.student_identity.academic_scope}",
            f"normalized_concept={strategy.normalized_concept}",
            f"normalization_status={strategy.normalization_status}",
            f"teaching_mode={strategy.pedagogy_strategy.teaching_mode}",
            f"intent_type={strategy.pedagogy_strategy.intent_type}",
            f"rag_mode={rag_context.mode}",
            f"source_tags={list(rag_context.source_tags)}",
            f"language_guidance={language_guidance}",
            "retrieved_context:",
            context_text,
            "math_grounding:",
            math_context,
        ]
    )

    return (
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    )


def build_local_tutor_fallback(request: Any, strategy: Any, rag_context: Any) -> str:
    """Return a safe local teaching response when the model path is unavailable."""
    raw_input = request.current_interaction_context.raw_whiteboard_input
    concept = strategy.normalized_concept or "this maths topic"

    if strategy.pedagogy_strategy.response_format == "micro_clarification":
        return "Which maths topic should we work on? Send the question or name the topic."

    if _looks_like_pidgin(raw_input):
        return (
            f"No wahala. For {concept}, start by writing wetin the question give you, "
            "then isolate the unknown step by step. If it is an equation, move constants "
            "with inverse operations and check your answer by substituting it back."
        )

    if rag_context.context_text.strip():
        return (
            f"Let's use the verified {concept} context. First identify the unknown, "
            "then use inverse operations to isolate it. After calculating, substitute "
            "the value back into the original question to check it."
        )

    return (
        f"I can help with {concept}. Start by listing the given values and what the "
        "question asks for, then choose the rule or formula that connects them."
    )


def _fallback_result(
    request: Any,
    strategy: Any,
    rag_context: Any,
    reason: str,
) -> TutorResponseResult:
    return TutorResponseResult(
        text=build_local_tutor_fallback(request, strategy, rag_context),
        llm_result=None,
        used_fallback=True,
        fallback_reason=reason,
    )


def _looks_like_pidgin(text: str) -> bool:
    normalized = f" {text.lower()} "
    return any(signal in normalized for signal in PIDGIN_SIGNALS)
