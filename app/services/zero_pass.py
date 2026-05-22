"""Layer 1 deterministic zero-pass handling.

Zero-pass is intentionally tiny: it handles Node-owned MCQ answer checks before
the request spends time in RAG or model execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


AnswerStatus = Literal["correct", "incorrect"]
ZeroPassReason = Literal["zero_pass_mcq_correct", "zero_pass_mcq_incorrect"]


@dataclass(frozen=True)
class ZeroPassResult:
    selected_answer: str
    correct_answer: str
    status: AnswerStatus
    reason: ZeroPassReason
    tutor_text: str
    micro_rewards: dict[str, int | str | None]
    concept_key: str | None

    @property
    def is_correct(self) -> bool:
        return self.status == "correct"


def evaluate_zero_pass(request: Any) -> ZeroPassResult | None:
    """Return a deterministic MCQ result when Node sends a server-only answer key."""
    context = request.current_interaction_context
    correct_answer = context.correct_answer
    if correct_answer is None:
        return None

    selected_answer = context.raw_whiteboard_input.strip().upper()
    concept_key = context.topic_node or None
    is_correct = selected_answer == correct_answer
    status: AnswerStatus = "correct" if is_correct else "incorrect"
    reason: ZeroPassReason = (
        "zero_pass_mcq_correct" if is_correct else "zero_pass_mcq_incorrect"
    )

    return ZeroPassResult(
        selected_answer=selected_answer,
        correct_answer=correct_answer,
        status=status,
        reason=reason,
        tutor_text=_build_tutor_text(
            selected_answer=selected_answer,
            correct_answer=correct_answer,
            status=status,
            concept_key=concept_key,
        ),
        micro_rewards=_build_micro_rewards(status),
        concept_key=concept_key,
    )


def _build_tutor_text(
    *,
    selected_answer: str,
    correct_answer: str,
    status: AnswerStatus,
    concept_key: str | None,
) -> str:
    topic_text = _topic_text(concept_key)
    if status == "correct":
        return (
            f"Correct. {selected_answer} is the answer for {topic_text}. "
            "Keep the method: identify what the question asks for, remove the "
            "impossible options, then verify the selected option against your working."
        )

    return (
        f"Not quite. You chose {selected_answer}, but the correct answer is "
        f"{correct_answer}. For {topic_text}, reread the question, write the rule "
        "or formula first, then test each option against the condition before choosing."
    )


def _build_micro_rewards(status: AnswerStatus) -> dict[str, int | str | None]:
    if status == "correct":
        return {
            "trigger_animation": "correct_answer",
            "praise_type": "accuracy",
            "xp_boost_awarded": 1,
        }

    return {
        "trigger_animation": None,
        "praise_type": "retry",
        "xp_boost_awarded": 0,
    }


def _topic_text(concept_key: str | None) -> str:
    if not concept_key:
        return "this question"
    return concept_key.replace("_", " ")
