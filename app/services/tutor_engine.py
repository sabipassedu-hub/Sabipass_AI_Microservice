"""Layer 5/6 tutor orchestration for strategy-bound response generation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json
import re
from typing import Any

from app.core.config import get_settings
from app.services.llm_executor import (
    CompletionCallable,
    LLMExecutionRequest,
    LLMExecutionResult,
    ModelCapacityError,
    ModelCircuitOpenError,
    ModelProviderError,
    ModelTimeoutError,
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
LINEAR_EQUATION_PRACTICE = (
    "2x + 5 = 13\nWhat is x?",
    "3x + 6 = 15\nWhat is x?",
    "3x + 9 = 18\nWhat is x?",
    "4x - 3 = 13\nWhat is x?",
    "5x + 2 = 3x + 14\nWhat is x?",
)
LINEAR_EQUATION_PATTERN = re.compile(
    r"(?:\b\d*\s*x\s*(?:[+\-]\s*\d+)?\s*=\s*-?\d+\b)|"
    r"(?:\b-?\d+\s*=\s*\d*\s*x\s*(?:[+\-]\s*\d+)?\b)",
    re.IGNORECASE,
)


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
    if strategy.pedagogy_strategy.response_format == "micro_clarification":
        return _fallback_result(request, strategy, rag_context, "clarification_required")

    math_result = verify_math_request(
        request.current_interaction_context.raw_whiteboard_input,
        concept_key=strategy.normalized_concept,
    )
    if get_settings().sabi_demo_mode:
        demo_response = build_demo_tutor_response(
            request,
            strategy,
            rag_context,
            math_result=math_result,
        )
        if demo_response is not None:
            return TutorResponseResult(
                text=demo_response,
                llm_result=None,
                used_fallback=False,
                math_status=math_result.status,
                math_source=math_result.source,
            )

    if model_route is None:
        return _fallback_result(
            request,
            strategy,
            rag_context,
            "model_route_unavailable",
            math_result=math_result,
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
        return _fallback_result(
            request,
            strategy,
            rag_context,
            _fallback_reason_for_exception(exc),
            math_result=math_result,
        )

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
        "Render the supplied action only. Do not invent exam facts. "
        "Do not choose intent, action, phase, correctness, progression, attempts, "
        "streaks, mastery, or next phase. "
        "Never ask for a topic when topic, subtopic, micro_skill, normalized_concept, "
        "or learning_topic is present. Follow response_contract exactly. "
        "When math_grounding is provided, do not contradict it."
    )
    learning_state = getattr(strategy, "learning_state", None)
    state_control = getattr(strategy, "state_control", None) or {}
    action_plan = getattr(strategy, "action_plan", None)
    response_contract = _response_contract(request, strategy)
    selected_question = _selected_practice_question(strategy)
    student_context = {
        "raw_input": raw_input,
        "phase": getattr(learning_state, "phase", None),
        "attempt": getattr(learning_state, "attempt", None),
        "streak": getattr(learning_state, "streak", None),
        "difficulty_level": getattr(learning_state, "difficulty_level", None),
        "active_equation": _active_equation_text(request),
        "candidate_answer": getattr(action_plan, "candidate_answer", None),
        "action_reason": getattr(action_plan, "reason", None),
    }
    user_message = "\n".join(
        [
            "llm_renderer_contract:",
            json.dumps(
                {
                    "action": getattr(action_plan, "action_type", None),
                    "topic": getattr(learning_state, "topic", None),
                    "subtopic": getattr(learning_state, "subtopic", None),
                    "micro_skill": getattr(learning_state, "micro_skill", None),
                    "student_context": student_context,
                },
                sort_keys=True,
            ),
            f"student_input={raw_input}",
            f"exam_target={request.student_identity.exam_target}",
            f"academic_scope={request.student_identity.academic_scope}",
            f"normalized_concept={strategy.normalized_concept}",
            f"normalization_status={strategy.normalization_status}",
            f"action={getattr(action_plan, 'action_type', None)}",
            f"action_reason={getattr(action_plan, 'reason', None)}",
            f"state_mutation_allowed={getattr(action_plan, 'state_mutation_allowed', None)}",
            f"candidate_answer={getattr(action_plan, 'candidate_answer', None)}",
            f"intent_scores={getattr(action_plan, 'intent_scores', None)}",
            f"teaching_mode={strategy.pedagogy_strategy.teaching_mode}",
            f"intent_type={strategy.pedagogy_strategy.intent_type}",
            f"learning_topic={getattr(learning_state, 'topic', None)}",
            f"learning_subtopic={getattr(learning_state, 'subtopic', None)}",
            f"learning_phase={getattr(learning_state, 'phase', None)}",
            f"learning_attempt={getattr(learning_state, 'attempt', None)}",
            f"learning_streak={getattr(learning_state, 'streak', None)}",
            f"learning_micro_skill={getattr(learning_state, 'micro_skill', None)}",
            f"difficulty_level={getattr(learning_state, 'difficulty_level', None)}",
            f"latest_correctness={_latest_correctness(learning_state)}",
            f"system_next_phase={state_control.get('next_phase')}",
            f"system_progression_recommendation={state_control.get('progression_recommendation')}",
            "progression_authority=system_only",
            "response_contract:",
            response_contract,
            "system_selected_practice_question:",
            selected_question,
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


def build_demo_tutor_response(
    request: Any,
    strategy: Any,
    rag_context: Any,
    *,
    math_result: MathVerificationResult | None = None,
) -> str | None:
    """Return polished deterministic text for the scripted investor demo matrix."""
    raw_input = request.current_interaction_context.raw_whiteboard_input
    normalized = _normalize_demo_text(raw_input)
    mode = str(getattr(request, "app_execution_mode", ""))
    concept = strategy.normalized_concept or request.current_interaction_context.topic_node

    if "x^2 - 5x + 6" in normalized or concept == "quadratic_equations":
        return (
            "Put the quadratic in the form x^2 - 5x + 6 = 0. Now find two numbers "
            "that multiply to 6 and add to -5: they are -2 and -3. So it factorises "
            "as (x - 2)(x - 3) = 0, which means x = 2 or x = 3. To check, substitute "
            "each root back into the original equation and both make the expression zero."
        )

    if "sqrt(50)" in normalized or "surd" in normalized or concept == "surds":
        return (
            "sqrt(50) can be split into sqrt(25 x 2). Since sqrt(25) = 5, the "
            "simplified answer is 5sqrt(2). In WAEC or JAMB, look first for the "
            "largest square factor inside the root, then take that square factor outside."
        )

    if mode == "curriculum_coach":
        if "subtract 4" in normalized:
            return (
                "We subtract 4 from both sides because the equation must stay balanced. "
                "In 2x + 4 = 10, the +4 is attached to the x side, so subtracting 4 "
                "undoes it: 2x = 6. Then divide both sides by 2, so x = 3."
            )
        if "practice" in normalized:
            return (
                "Try this SS1 practice question: solve 3x + 5 = 20. First subtract 5 "
                "from both sides to get 3x = 15. Then divide by 3, so x = 5. Your check "
                "is 3(5) + 5 = 20."
            )
        return (
            "Linear equations are equations where the unknown has power 1, like "
            "2x + 4 = 10. The main skill is balance: whatever you do to one side, "
            "you do to the other. Example: subtract 4 to get 2x = 6, divide by 2, "
            "and the answer is x = 3."
        )

    if mode == "homework_explainer":
        if "5x - 7 = 18" in normalized:
            return (
                "For 5x - 7 = 18, first add 7 to both sides: 5x = 25. Then divide "
                "both sides by 5, so x = 5. Check it: 5(5) - 7 = 18."
            )
        if "3x + 6 = 18" in normalized:
            return (
                "Your answer x = 4 is correct. Check: 3(4) + 6 = 12 + 6 = 18. "
                "The method is to subtract 6 first, then divide by 3."
            )
        if "hints only" in normalized or "hint mode" in normalized:
            return (
                "Hint 1: in 4x + 5 = 21, undo the +5 first. Hint 2: after that, "
                "you will have 4x alone on the left. Hint 3: divide both sides by "
                "the number beside x."
            )

    if "2x + 4 = 10" in normalized:
        return (
            "No wahala. For 2x + 4 = 10, first subtract 4 from both sides: 2x = 6. "
            "Then divide both sides by 2, so x = 3. Check am: 2(3) + 4 = 10."
        )

    if (
        math_result is not None
        and math_result.response_text is not None
        and concept in {"linear_equations", "quadratic_equations", "surds", "algebra"}
    ):
        return math_result.response_text

    if concept in {"linear_equations", "algebra", "general_mathematics"} and (
        "linear equation" in normalized or "find x" in normalized or "solve" in normalized
    ):
        return (
            "Start by identifying the unknown, then use inverse operations to keep "
            "the equation balanced. Move constants away from x first, divide by the "
            "coefficient of x, and always substitute your answer back to check it."
        )

    if rag_context.context_text.strip() and concept:
        return (
            f"Let's use the verified {concept.replace('_', ' ')} material. First, "
            "write what the question gives you, then choose the rule that connects "
            "those values and check the answer against the original question."
        )

    return None


def build_local_tutor_fallback(
    request: Any,
    strategy: Any,
    rag_context: Any,
    *,
    math_result: MathVerificationResult | None = None,
) -> str:
    """Return a safe local teaching response when the model path is unavailable."""
    raw_input = request.current_interaction_context.raw_whiteboard_input
    concept = strategy.normalized_concept or "this maths topic"

    structured_response = _build_structured_local_response(request, strategy)
    if structured_response is not None:
        return structured_response

    if math_result is not None and math_result.response_text is not None:
        if _looks_like_pidgin(raw_input):
            return f"No wahala. {math_result.response_text}"
        return math_result.response_text

    if strategy.pedagogy_strategy.response_format == "micro_clarification":
        state_concept = _state_concept_label(strategy)
        if state_concept is not None:
            return (
                f"I'm still with {state_concept}. Send the exact step, answer, or "
                "line you want checked, and I'll keep us on this same topic."
            )
        return "Send the exact maths question or step you want help with."

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


def _response_contract(request: Any, strategy: Any) -> str:
    learning_state = getattr(strategy, "learning_state", None)
    phase = getattr(learning_state, "phase", None)
    intent_type = getattr(strategy.pedagogy_strategy, "intent_type", None)
    latest_correct = _latest_correctness_value(learning_state)
    action_type = _action_type(strategy)

    if strategy.pedagogy_strategy.response_format == "micro_clarification":
        if _state_concept_label(strategy) is not None:
            return (
                "CLARIFICATION: stay on the known learning topic; ask for the exact "
                "step, answer, or line to check. Do not ask which topic to study."
            )
        return "CLARIFICATION: ask for the exact maths question or step."

    if action_type == "explain_step":
        return (
            "EXPLAIN_STEP: explain only the current step in the current question. "
            "Reference the current equation if available. Do not restart the lesson, "
            "do not give a generic topic overview, and do not grade any candidate "
            "answer in the same turn."
        )

    if action_type == "give_hint":
        return (
            "GIVE_HINT: give one targeted hint for the active question. Do not reveal "
            "the full solution, change phase, or ask an open-ended topic question."
        )

    if action_type == "intervention":
        return (
            "INTERVENTION: identify the weakest visible micro-skill and offer bounded "
            "recovery options only: relearn foundation, guided walkthrough mode, or "
            "simplified examples."
        )

    if action_type == "grade_answer" and latest_correct is True:
        return (
            "GRADE_ANSWER: acknowledge the system-provided correctness briefly, "
            "then follow the system-selected progression note. Do not declare "
            "mastery or unlocks as final record."
        )

    if action_type == "grade_answer" or latest_correct is False or phase == "intervention":
        return (
            "CORRECTION: identify the likely error, show the correct next steps, "
            "then end with exactly one retry question. Do not change topic."
        )

    if phase == "explanation" or intent_type == "explanation":
        return (
            "EXPLANATION: include a Concept section, one everyday analogy, one "
            "worked example, and end with exactly one practice question selected "
            "by the system. Do not add extra questions."
        )

    if phase == "guided_example":
        return (
            "GUIDED_EXAMPLE: show one worked example step by step, then end with "
            "exactly one similar practice question selected by the system."
        )

    if phase in {"practice", "evaluation"}:
        if latest_correct is True:
            return (
                "PRACTICE: briefly acknowledge the system-provided correctness, "
                "mention progress from mastery if useful, and end with exactly "
                "one system-selected next question."
            )
        return (
            "PRACTICE: give exactly one system-selected question only. Do not "
            "explain unless the system marked the previous answer incorrect."
        )

    return (
        "TUTORING: stay on the known topic, teach the next reliable step, and "
        "do not ask the student to choose a new topic."
    )


def _build_structured_local_response(request: Any, strategy: Any) -> str | None:
    if strategy.pedagogy_strategy.response_format == "micro_clarification":
        return None

    learning_state = getattr(strategy, "learning_state", None)
    phase = getattr(learning_state, "phase", None)
    intent_type = getattr(strategy.pedagogy_strategy, "intent_type", None)
    latest_correct = _latest_correctness_value(learning_state)
    action_type = _action_type(strategy)

    if not _is_linear_concept(strategy):
        return None

    if action_type == "explain_step":
        return _linear_step_explanation_response(request)

    if action_type == "give_hint":
        return _linear_hint_response(request, strategy)

    if action_type == "intervention":
        return _linear_intervention_response(strategy)

    if action_type == "guided_example":
        return _linear_guided_example_response(request, strategy)

    if action_type == "give_practice":
        return _selected_practice_question(strategy)

    if action_type == "grade_answer":
        if latest_correct is True:
            return _linear_correct_practice_response(strategy)
        if latest_correct is False:
            return _linear_correction_response(request, strategy)
        return _linear_candidate_stored_response(strategy)

    if latest_correct is False or phase == "intervention":
        return _linear_correction_response(request, strategy)

    if phase == "explanation" or intent_type == "explanation":
        return _linear_explanation_response(request, strategy)

    if phase == "guided_example":
        return _linear_guided_example_response(request, strategy)

    if phase in {"practice", "evaluation"}:
        if latest_correct is True:
            return _linear_correct_practice_response(strategy)
        return _selected_practice_question(strategy)

    return None


def _linear_step_explanation_response(request: Any) -> str:
    raw_input = request.current_interaction_context.raw_whiteboard_input
    prefix = "No wahala. " if _looks_like_pidgin(raw_input) else ""
    equation = _active_equation_text(request)
    subtract_value = _operation_value(raw_input, "subtract")
    divide_value = _operation_value(raw_input, "divide")

    if subtract_value is not None:
        equation_text = f"In {equation}, " if equation else "In the current equation, "
        return (
            f"{prefix}{equation_text}we subtract {subtract_value} because that undoes "
            f"the +{subtract_value} on the x side while keeping both sides balanced. "
            f"The step is: left side - {subtract_value}, right side - {subtract_value}. "
            f"So the +{subtract_value} and -{subtract_value} combine to 0; the number "
            "did not disappear, it was cancelled by the inverse operation."
        )

    if divide_value is not None:
        equation_text = f"In {equation}, " if equation else "In the current equation, "
        return (
            f"{prefix}{equation_text}we divide by {divide_value} because x is being "
            f"multiplied by {divide_value}. Dividing both sides by {divide_value} "
            "keeps the equation balanced and leaves x by itself."
        )

    equation_text = f" for {equation}" if equation else ""
    return (
        f"{prefix}Let's stay on this exact linear-equation step{equation_text}. "
        "Use the inverse operation on both sides so the equation stays balanced, "
        "then simplify only that line before moving to the next step."
    )


def _linear_hint_response(request: Any, strategy: Any) -> str:
    prefix = "No wahala. " if _looks_like_pidgin(
        request.current_interaction_context.raw_whiteboard_input
    ) else ""
    equation = _active_equation_text(request)
    target = f" in {equation}" if equation else ""
    return (
        f"{prefix}Hint{target}: undo the constant term first, and do the same "
        "operation to both sides. After that, look at the number multiplying x."
    )


def _linear_intervention_response(strategy: Any) -> str:
    learning_state = getattr(strategy, "learning_state", None)
    micro_skill = str(
        getattr(learning_state, "micro_skill", None)
        or "linear equation balancing"
    ).replace("_", " ")
    return (
        f"We need a short reset on {micro_skill}. Choose one recovery path: "
        "relearn foundation, guided walkthrough mode, or simplified examples."
    )


def _linear_candidate_stored_response(strategy: Any) -> str:
    action_plan = getattr(strategy, "action_plan", None)
    candidate_answer = getattr(action_plan, "candidate_answer", None)
    if candidate_answer is None:
        return _selected_practice_question(strategy)
    return (
        f"I have noted your candidate answer as x = {candidate_answer}. "
        "I will grade it only on this evaluation action, using the active question "
        "and the system's correctness rules."
    )


def _linear_explanation_response(request: Any, strategy: Any) -> str:
    prefix = "No wahala. " if _looks_like_pidgin(request.current_interaction_context.raw_whiteboard_input) else ""
    return (
        f"{prefix}Let's stay on Linear Equations.\n\n"
        "Concept:\n"
        "A linear equation is an equation where the highest power of x is 1.\n\n"
        "Analogy:\n"
        "Think of it like a balance scale. Whatever you do to one side, you must "
        "do to the other side so both sides stay equal.\n\n"
        "Example:\n"
        "2x + 4 = 10\n"
        "Subtract 4 from both sides:\n"
        "2x = 6\n"
        "Divide both sides by 2:\n"
        "x = 3\n\n"
        "Now try:\n"
        f"{_selected_practice_question(strategy)}"
    )


def _linear_guided_example_response(request: Any, strategy: Any) -> str:
    prefix = "No wahala. " if _looks_like_pidgin(request.current_interaction_context.raw_whiteboard_input) else ""
    return (
        f"{prefix}Let's work one example together.\n\n"
        "Example:\n"
        "3x + 6 = 15\n"
        "Step 1: subtract 6 from both sides.\n"
        "3x = 9\n"
        "Step 2: divide both sides by 3.\n"
        "x = 3\n\n"
        "Now try:\n"
        f"{_selected_practice_question(strategy)}"
    )


def _linear_correct_practice_response(strategy: Any) -> str:
    mastery_percent = _mastery_percent(strategy)
    return (
        "Nice - correct.\n\n"
        "You isolated x properly.\n\n"
        f"Progress: {mastery_percent}%\n\n"
        "Next:\n"
        f"{_selected_practice_question(strategy)}"
    )


def _linear_correction_response(request: Any, strategy: Any) -> str:
    prefix = "No wahala, let's fix it together.\n\n" if _looks_like_pidgin(
        request.current_interaction_context.raw_whiteboard_input
    ) else "Not quite - let's fix it together.\n\n"
    return (
        prefix +
        "For a question like 3x + 6 = 15, the common mistake is to stop before "
        "dividing by the number beside x.\n\n"
        "Step 1: subtract 6 from both sides.\n"
        "3x = 9\n\n"
        "Step 2: divide both sides by 3.\n"
        "x = 3\n\n"
        "Try again:\n"
        f"{_selected_practice_question(strategy)}"
    )


def _selected_practice_question(strategy: Any) -> str:
    if not _is_linear_concept(strategy):
        concept = strategy.normalized_concept or "this topic"
        return f"Give one example from {concept.replace('_', ' ')} and tell me the next step."

    learning_state = getattr(strategy, "learning_state", None)
    attempt = int(getattr(learning_state, "attempt", 0) or 0)
    difficulty = getattr(learning_state, "difficulty_level", "easy")
    latest_correct = _latest_correctness_value(learning_state)

    if latest_correct is False:
        index = min(max(attempt, 2), len(LINEAR_EQUATION_PRACTICE) - 1)
    elif difficulty == "hard":
        index = len(LINEAR_EQUATION_PRACTICE) - 1
    elif difficulty == "medium":
        index = min(max(attempt, 3), len(LINEAR_EQUATION_PRACTICE) - 1)
    else:
        index = min(max(attempt, 0), len(LINEAR_EQUATION_PRACTICE) - 1)

    return LINEAR_EQUATION_PRACTICE[index]


def _latest_correctness(learning_state: Any) -> str:
    latest = _latest_correctness_value(learning_state)
    if latest is True:
        return "correct"
    if latest is False:
        return "incorrect"
    return "unknown"


def _latest_correctness_value(learning_state: Any) -> bool | None:
    pattern = getattr(learning_state, "correct_pattern", None)
    if not pattern:
        return None
    return bool(pattern[-1])


def _mastery_percent(strategy: Any) -> int:
    learning_state = getattr(strategy, "learning_state", None)
    mastery_score = float(getattr(learning_state, "mastery_score", 0.0) or 0.0)
    return round(max(0.0, min(1.0, mastery_score)) * 100)


def _action_type(strategy: Any) -> str | None:
    action_plan = getattr(strategy, "action_plan", None)
    return getattr(action_plan, "action_type", None)


def _active_equation_text(request: Any) -> str | None:
    context = getattr(request, "current_interaction_context", None)
    if context is None:
        return None

    candidates = [getattr(context, "raw_whiteboard_input", "")]
    candidates.extend(reversed(getattr(context, "history_tokens", ()) or ()))
    for candidate in candidates:
        match = LINEAR_EQUATION_PATTERN.search(str(candidate))
        if match:
            return " ".join(match.group(0).split())
    return None


def _operation_value(text: str, operation: str) -> str | None:
    normalized = text.lower()
    operation_pattern = {
        "subtract": r"subtract(?:ing)?",
        "divide": r"divid(?:e|ing)",
    }.get(operation, re.escape(operation))
    match = re.search(rf"\b{operation_pattern}\s+([-+]?\d+(?:\.\d+)?)\b", normalized)
    if match:
        return match.group(1)
    return None


def _is_linear_concept(strategy: Any) -> bool:
    concept = strategy.normalized_concept
    learning_state = getattr(strategy, "learning_state", None)
    state_keys = {
        getattr(learning_state, "topic", None),
        getattr(learning_state, "subtopic", None),
        getattr(learning_state, "micro_skill", None),
    }
    return concept in {"linear_equations", "solving_basic_equations"} or bool(
        state_keys & {"linear_equations", "solving_basic_equations"}
    )


def _state_concept_label(strategy: Any) -> str | None:
    learning_state = getattr(strategy, "learning_state", None)
    for value in (
        getattr(learning_state, "subtopic", None),
        getattr(learning_state, "topic", None),
        strategy.normalized_concept,
    ):
        if value:
            return str(value).replace("_", " ").title()
    return None


def _fallback_result(
    request: Any,
    strategy: Any,
    rag_context: Any,
    reason: str,
    *,
    math_result: MathVerificationResult | None = None,
) -> TutorResponseResult:
    return TutorResponseResult(
        text=build_local_tutor_fallback(
            request,
            strategy,
            rag_context,
            math_result=math_result,
        ),
        llm_result=None,
        used_fallback=True,
        fallback_reason=reason,
        math_status=math_result.status if math_result is not None else "unsupported",
        math_source=math_result.source if math_result is not None else "none",
    )


def _fallback_reason_for_exception(exc: Exception) -> str:
    if isinstance(exc, ModelCapacityError):
        return "llm_capacity_exhausted"
    if isinstance(exc, ModelCircuitOpenError):
        return "llm_circuit_open"
    if isinstance(exc, ModelTimeoutError):
        return "llm_timeout"
    if isinstance(exc, ModelProviderError):
        return "llm_provider_error"
    return "llm_execution_error"


def _looks_like_pidgin(text: str) -> bool:
    normalized = f" {text.lower()} "
    return any(signal in normalized for signal in PIDGIN_SIGNALS)


def _normalize_demo_text(text: str) -> str:
    return " ".join(text.lower().replace("−", "-").split())
