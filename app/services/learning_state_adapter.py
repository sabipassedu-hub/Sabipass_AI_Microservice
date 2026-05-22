"""Strict learning-state machine validation.

This module keeps progression deterministic. Node persists state, Python
validates and normalizes the restored snapshot, and the LLM only executes the
resulting teaching strategy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from app.schemas.requests import LearningSessionState


TransitionStatus = Literal["valid", "normalized"]
ProgressionRecommendation = Literal[
    "continue_current_phase",
    "next_phase",
    "intervention_required",
    "next_micro_skill_unlocked",
]

PHASE_NEXT = {
    "explanation": "guided_example",
    "guided_example": "practice",
    "practice": "practice",
    "evaluation": "intervention",
    "intervention": "practice",
}
NO_SCORE_PHASES = {"explanation", "guided_example"}
FAST_GUESS_MS = 3_000
PRACTICE_MAX_ATTEMPT = 5
PRACTICE_MIN_EVALUATION_ATTEMPT = 3
MASTERY_UNLOCK_THRESHOLD = 0.70


class LearningStateValidationError(ValueError):
    """Raised when a restored learning state cannot safely enter the pipeline."""


@dataclass(frozen=True)
class LearningStateControlResult:
    state: LearningSessionState
    status: TransitionStatus
    issues: tuple[str, ...]
    next_phase: str
    progression_recommendation: ProgressionRecommendation
    state_mutation_allowed: bool
    anti_guessing_signal: str
    mastery_weight_multiplier: float

    def metadata(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "issues": list(self.issues),
            "topic": self.state.topic,
            "subtopic": self.state.subtopic,
            "micro_skill": self.state.micro_skill,
            "phase": self.state.phase,
            "attempt": self.state.attempt,
            "streak": self.state.streak,
            "mastery_score": self.state.mastery_score,
            "state_version": self.state.state_version,
            "current_question_id": self.state.current_question_id,
            "last_question_ids": list(self.state.last_question_ids),
            "correct_pattern": list(self.state.correct_pattern),
            "confidence_level": self.state.confidence_level,
            "response_time_ms": self.state.response_time_ms,
            "hints_used": self.state.hints_used,
            "difficulty_level": self.state.difficulty_level,
            "is_retention_check": self.state.is_retention_check,
            "next_phase": self.next_phase,
            "progression_recommendation": self.progression_recommendation,
            "state_mutation_allowed": self.state_mutation_allowed,
            "anti_guessing_signal": self.anti_guessing_signal,
            "mastery_weight_multiplier": self.mastery_weight_multiplier,
            "llm_controls_progression": False,
        }


def validate_and_normalize_learning_state(
    request: Any,
    *,
    registry_snapshot: dict,
) -> LearningStateControlResult:
    state = request.learning_session_state
    issues: list[str] = []

    _validate_curriculum_membership(state, registry_snapshot)
    _validate_context_alignment(request, state)
    state = _normalize_attempt_if_needed(state, issues)
    _validate_intervention_trigger(state)

    anti_guessing_signal, weight_multiplier = _anti_guessing_result(state)
    if anti_guessing_signal != "none":
        issues.append(anti_guessing_signal)

    next_phase, recommendation = _deterministic_transition(state)
    return LearningStateControlResult(
        state=state,
        status="normalized" if issues else "valid",
        issues=tuple(issues),
        next_phase=next_phase,
        progression_recommendation=recommendation,
        state_mutation_allowed=True,
        anti_guessing_signal=anti_guessing_signal,
        mastery_weight_multiplier=weight_multiplier,
    )


def _validate_curriculum_membership(
    state: LearningSessionState,
    registry_snapshot: dict,
) -> None:
    canonical_keys = registry_snapshot.get("canonical_keys") or {}
    for field_name in ("topic", "subtopic", "micro_skill"):
        value = getattr(state, field_name)
        if value not in canonical_keys:
            raise LearningStateValidationError(f"{field_name} is not in curriculum")

    if not _is_same_or_descendant(state.subtopic, state.topic, canonical_keys):
        raise LearningStateValidationError("subtopic does not belong to topic")
    if not _is_same_or_descendant(state.micro_skill, state.subtopic, canonical_keys):
        raise LearningStateValidationError("micro_skill does not belong to subtopic")


def _validate_context_alignment(request: Any, state: LearningSessionState) -> None:
    topic_node = getattr(request.current_interaction_context, "topic_node", "")
    if not topic_node:
        return
    if topic_node in {state.topic, state.subtopic, state.micro_skill}:
        return
    raise LearningStateValidationError("topic_node does not match learning state")


def _is_same_or_descendant(child: str, ancestor: str, canonical_keys: dict[str, dict]) -> bool:
    if child == ancestor:
        return True

    current = child
    visited: set[str] = set()
    while current and current not in visited:
        visited.add(current)
        parent = canonical_keys.get(current, {}).get("parent_key")
        if parent == ancestor:
            return True
        current = parent

    return False


def _normalize_attempt_if_needed(
    state: LearningSessionState,
    issues: list[str],
) -> LearningSessionState:
    normalized_attempt = state.attempt

    if state.phase in NO_SCORE_PHASES and state.attempt != 0:
        normalized_attempt = 0
        issues.append("attempt_normalized_for_no_score_phase")

    if state.phase == "practice":
        observed_attempts = max(len(state.last_question_ids), len(state.correct_pattern))
        max_expected_attempt = min(PRACTICE_MAX_ATTEMPT, observed_attempts + 1)
        if state.attempt > max_expected_attempt:
            normalized_attempt = max_expected_attempt
            issues.append("attempt_jump_normalized")

    if normalized_attempt == state.attempt:
        return state
    return state.model_copy(update={"attempt": normalized_attempt})


def _validate_intervention_trigger(state: LearningSessionState) -> None:
    if state.phase != "intervention":
        return
    if state.attempt >= 3 or _streak_broken_repeatedly(state):
        return
    raise LearningStateValidationError("intervention requires repeated struggle evidence")


def _streak_broken_repeatedly(state: LearningSessionState) -> bool:
    recent = list(state.correct_pattern[-4:])
    return recent.count(False) >= 2


def _anti_guessing_result(state: LearningSessionState) -> tuple[str, float]:
    if not state.correct_pattern or state.correct_pattern[-1] is not True:
        return "none", 1.0

    low_confidence = state.confidence_level == "low"
    fast_response = (
        state.response_time_ms is not None
        and state.response_time_ms < FAST_GUESS_MS
    )
    inconsistent = {True, False}.issubset(set(state.correct_pattern[-4:]))

    if low_confidence and fast_response and inconsistent:
        return "guessing_risk_low_confidence_fast_inconsistent", 0.5

    if state.hints_used > 0:
        penalty = min(state.hints_used * 0.05, 0.3)
        return "hint_penalty_applied", round(1.0 - penalty, 3)

    return "none", 1.0


def _deterministic_transition(
    state: LearningSessionState,
) -> tuple[str, ProgressionRecommendation]:
    if state.phase == "explanation":
        return "guided_example", "next_phase"
    if state.phase == "guided_example":
        return "practice", "next_phase"
    if state.phase == "practice":
        if state.attempt >= 3 and _streak_broken_repeatedly(state):
            return "intervention", "intervention_required"
        if state.attempt >= PRACTICE_MIN_EVALUATION_ATTEMPT and state.streak >= 2:
            return "evaluation", "next_phase"
        return "practice", "continue_current_phase"
    if state.phase == "evaluation":
        if state.mastery_score >= MASTERY_UNLOCK_THRESHOLD:
            return "explanation", "next_micro_skill_unlocked"
        return "intervention", "intervention_required"
    if state.phase == "intervention":
        return "practice", "next_phase"

    raise LearningStateValidationError("unsupported phase")
