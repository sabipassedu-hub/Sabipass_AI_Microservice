"""Deterministic tutor action resolver.

Intent answers what the student is trying to do. This layer answers what the
engine will do next from intent plus restored learning state. It contains no
LLM calls and performs no final response wording.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from app.services.strategy.intent_parser import IntentResult


ActionType = Literal[
    "explain_step",
    "guided_example",
    "give_practice",
    "grade_answer",
    "give_hint",
    "intervention",
]


@dataclass(frozen=True)
class TutorActionPlan:
    """System-selected tutor action for downstream renderers."""

    action_type: ActionType
    intent_type: str
    intent_scores: dict[str, float]
    confidence: float
    candidate_answer: str | None
    state_mutation_allowed: bool
    next_phase: str
    progression_recommendation: str
    reason: str
    state_effect: str = "none"

    def metadata(self) -> dict[str, Any]:
        return {
            "action": self.action_type,
            "intent": self.intent_type,
            "intent_scores": dict(self.intent_scores),
            "intent_confidence": self.confidence,
            "candidate_answer": self.candidate_answer,
            "state_mutation_allowed": self.state_mutation_allowed,
            "next_phase": self.next_phase,
            "progression_recommendation": self.progression_recommendation,
            "reason": self.reason,
            "state_effect": self.state_effect,
        }


def resolve_tutor_action(
    *,
    intent: IntentResult,
    learning_state: Any,
) -> TutorActionPlan:
    """Resolve the system action from intent and state only."""
    phase = str(getattr(learning_state, "phase", "") or "practice")
    attempt = int(getattr(learning_state, "attempt", 0) or 0)
    latest_correct = _latest_correctness_value(learning_state)
    scores = intent.intent_scores or {
        "explanation": 0.0,
        "confusion": 0.0,
        "evaluation": 0.0,
    }

    if attempt >= 4:
        return _plan(
            intent=intent,
            scores=scores,
            action_type="intervention",
            phase=phase,
            state_mutation_allowed=False,
            progression_recommendation="intervention_required",
            reason="attempt_threshold_reached",
        )

    if intent.intent_type == "explanation":
        return _plan(
            intent=intent,
            scores=scores,
            action_type="explain_step",
            phase=phase,
            state_mutation_allowed=False,
            progression_recommendation="continue_current_phase",
            reason=f"explanation_intent_in_{phase}_phase",
        )

    if intent.intent_type == "confusion":
        if attempt >= 3:
            return _plan(
                intent=intent,
                scores=scores,
                action_type="intervention",
                phase=phase,
                state_mutation_allowed=False,
                progression_recommendation="intervention_required",
                reason="confusion_after_repeated_attempts",
            )
        if phase in {"practice", "evaluation"}:
            return _plan(
                intent=intent,
                scores=scores,
                action_type="give_hint",
                phase=phase,
                state_mutation_allowed=False,
                progression_recommendation="continue_current_phase",
                reason=f"confusion_intent_in_{phase}_phase",
            )
        return _plan(
            intent=intent,
            scores=scores,
            action_type="guided_example",
            phase=phase,
            state_mutation_allowed=False,
            progression_recommendation="continue_current_phase",
            reason=f"confusion_intent_in_{phase}_phase",
        )

    if phase in {"practice", "evaluation"}:
        return _grade_plan(
            intent=intent,
            scores=scores,
            phase=phase,
            latest_correct=latest_correct,
        )
    if phase == "guided_example":
        return _plan(
            intent=intent,
            scores=scores,
            action_type="give_practice",
            phase=phase,
            state_mutation_allowed=False,
            progression_recommendation="continue_current_phase",
            reason="evaluation_like_input_after_guided_example",
        )
    return _plan(
        intent=intent,
        scores=scores,
        action_type="guided_example",
        phase=phase,
        state_mutation_allowed=False,
        progression_recommendation="continue_current_phase",
        reason=f"evaluation_like_input_in_{phase}_phase",
    )


def _grade_plan(
    *,
    intent: IntentResult,
    scores: dict[str, float],
    phase: str,
    latest_correct: bool | None,
) -> TutorActionPlan:
    if latest_correct is True:
        return _plan(
            intent=intent,
            scores=scores,
            action_type="grade_answer",
            phase=phase,
            state_mutation_allowed=True,
            progression_recommendation="next_phase",
            reason="evaluation_intent_with_correctness_evidence",
            state_effect="progress_forward",
        )
    if latest_correct is False:
        return _plan(
            intent=intent,
            scores=scores,
            action_type="grade_answer",
            phase=phase,
            state_mutation_allowed=True,
            progression_recommendation="continue_current_phase",
            reason="evaluation_intent_with_incorrectness_evidence",
            state_effect="record_retry",
        )
    return _plan(
        intent=intent,
        scores=scores,
        action_type="grade_answer",
        phase=phase,
        state_mutation_allowed=True,
        progression_recommendation="continue_current_phase",
        reason=f"evaluation_intent_in_{phase}_phase",
        state_effect="grade_candidate_answer",
    )


def _plan(
    *,
    intent: IntentResult,
    scores: dict[str, float],
    action_type: ActionType,
    phase: str,
    state_mutation_allowed: bool,
    progression_recommendation: str,
    reason: str,
    state_effect: str = "none",
) -> TutorActionPlan:
    return TutorActionPlan(
        action_type=action_type,
        intent_type=intent.intent_type,
        intent_scores=dict(scores),
        confidence=float(intent.confidence),
        candidate_answer=intent.candidate_answer,
        state_mutation_allowed=state_mutation_allowed,
        next_phase=phase if not state_mutation_allowed else _next_phase_for_action(action_type, phase),
        progression_recommendation=progression_recommendation,
        reason=reason,
        state_effect=state_effect,
    )


def _next_phase_for_action(action_type: str, phase: str) -> str:
    if action_type == "grade_answer":
        return phase
    if action_type == "intervention":
        return "intervention"
    return phase


def _latest_correctness_value(learning_state: Any) -> bool | None:
    pattern = getattr(learning_state, "correct_pattern", None)
    if not pattern:
        return None
    return bool(pattern[-1])
