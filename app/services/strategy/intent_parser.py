"""Layer 2 deterministic intent detector.

Purpose: classify the student's turn from restored learning state, input
structure, and keyword signals before any pedagogy/action/model routing.
Constraints: rule-based only, Pidgin-aware, no ML dependency, and no final
tutor text generation.
"""

from dataclasses import dataclass
import re
from typing import Any, Literal


IntentType = Literal["explanation", "confusion", "evaluation"]
Urgency = Literal["low", "normal", "high"]


INTENT_PRIORITY: tuple[IntentType, ...] = ("explanation", "confusion", "evaluation")
EXPLANATION_SIGNALS = (
    "why",
    "how",
    "explain",
    "what happened",
    "where did",
    "where does",
    "why are",
    "why do",
    "why did",
    "prove",
    "show me",
    "make i understand",
    "how e dey work",
    "wetin make",
    "abeg explain",
    "disappear",
    "cancel",
)
CONFUSION_SIGNALS = (
    "lost",
    "stuck",
    "confused",
    "confusing",
    "i don't understand",
    "i dont understand",
    "i do not understand",
    "i no understand",
    "no understand",
    "not getting",
    "i am tired",
    "i'm tired",
    "i don tire",
    "i give up",
    "i no fit",
    "wahala",
)
EVALUATION_SIGNALS = (
    "i think",
    "my answer",
    "answer is",
    "the answer is",
    "it is",
    "it's",
    "its",
    "i got",
    "i get",
    "x =",
)
MATH_COMMAND_SIGNALS = (
    "solve",
    "find x",
    "find the value",
    "calculate",
)
STEP_TERMS = (
    "add",
    "subtract",
    "minus",
    "divide",
    "multiply",
    "move",
    "cancel",
    "disappear",
    "both sides",
)
ANSWER_PATTERNS = (
    re.compile(r"\bx\s*=\s*([-+]?\d+(?:\.\d+)?(?:/\d+)?)\b"),
    re.compile(
        r"\b(?:i think|maybe|my answer is|answer is|the answer is|it is|it's|its|i got|get)\s+"
        r"(?:x\s*=\s*)?([-+]?\d+(?:\.\d+)?(?:/\d+)?)\b"
    ),
)
SIMPLE_ANSWER_PATTERN = re.compile(r"^(?:x\s*=\s*)?[-+]?\d+(?:\.\d+)?(?:/\d+)?$")


@dataclass(frozen=True)
class IntentResult:
    """State-first intent classification for strategy compilation."""

    intent_type: IntentType
    urgency: Urgency
    matched_signals: tuple[str, ...] = ()
    intent_scores: dict[str, float] | None = None
    confidence: float = 0.0
    candidate_answer: str | None = None


def parse_intent(
    raw_input: str,
    *,
    session_state: Any | None = None,
    current_interaction_context: Any | None = None,
) -> IntentResult:
    """Parse request intent without model calls."""
    text = _normalize_text(raw_input)
    scores = _empty_scores()
    if not text:
        scores["confusion"] = 0.2
        return _result(
            intent_type="confusion",
            urgency="low",
            matched_signals=(),
            scores=scores,
            candidate_answer=None,
        )

    phase = str(getattr(session_state, "phase", "") or "")
    active_question = _has_active_question(session_state, current_interaction_context)
    candidate_answer = _extract_candidate_answer(text)

    explanation_matches = _matched_signals(text, EXPLANATION_SIGNALS)
    confusion_matches = _matched_signals(text, CONFUSION_SIGNALS)
    evaluation_matches = _matched_signals(text, EVALUATION_SIGNALS)

    if explanation_matches:
        scores["explanation"] += 0.72
    if text.startswith(("why ", "how ", "where ", "what ")):
        scores["explanation"] = max(scores["explanation"], 0.9)
    if "?" in raw_input and _has_step_term(text):
        scores["explanation"] += 0.18
    if _has_math_command(text) and candidate_answer is None:
        scores["explanation"] = max(scores["explanation"], 0.55)

    if confusion_matches:
        scores["confusion"] += 0.74
    if phase in {"practice", "evaluation"} and active_question and confusion_matches:
        scores["confusion"] += 0.08

    if evaluation_matches:
        scores["evaluation"] += 0.52
    if candidate_answer is not None:
        scores["evaluation"] += 0.56
    if phase in {"practice", "evaluation"} and active_question and candidate_answer is not None:
        scores["evaluation"] += 0.18
    if phase == "evaluation" and active_question and _looks_like_answer_only(text):
        scores["evaluation"] = max(scores["evaluation"], 0.82)

    _apply_required_priority_when_mixed(
        scores,
        explanation_matches=explanation_matches,
        confusion_matches=confusion_matches,
        candidate_answer=candidate_answer,
    )

    if not any(scores.values()):
        if phase in {"practice", "evaluation"} and active_question:
            scores["confusion"] = 0.35
        else:
            scores["explanation"] = 0.35

    selected = _select_highest_score(scores)
    selected_matches = _selected_matches(
        selected,
        explanation_matches=explanation_matches,
        confusion_matches=confusion_matches,
        evaluation_matches=evaluation_matches,
        candidate_answer=candidate_answer,
    )

    return _result(
        intent_type=selected,
        urgency=_urgency_for(selected, scores[selected]),
        matched_signals=selected_matches,
        scores=scores,
        candidate_answer=candidate_answer,
    )


def _result(
    *,
    intent_type: IntentType,
    urgency: Urgency,
    matched_signals: tuple[str, ...],
    scores: dict[str, float],
    candidate_answer: str | None,
) -> IntentResult:
    rounded_scores = {
        intent: round(min(max(score, 0.0), 1.0), 3)
        for intent, score in scores.items()
    }
    return IntentResult(
        intent_type=intent_type,
        urgency=urgency,
        matched_signals=matched_signals,
        intent_scores=rounded_scores,
        confidence=rounded_scores[intent_type],
        candidate_answer=candidate_answer,
    )


def _empty_scores() -> dict[str, float]:
    return {"explanation": 0.0, "confusion": 0.0, "evaluation": 0.0}


def _has_active_question(
    session_state: Any | None,
    current_interaction_context: Any | None,
) -> bool:
    if session_state is None:
        return False
    if getattr(session_state, "current_question_id", None):
        return True
    if getattr(session_state, "phase", None) in {"practice", "evaluation"}:
        return True
    history_tokens = getattr(current_interaction_context, "history_tokens", None)
    return bool(history_tokens)


def _extract_candidate_answer(text: str) -> str | None:
    for pattern in ANSWER_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1).strip()

    if SIMPLE_ANSWER_PATTERN.fullmatch(text):
        return text.replace("x", "").replace("=", "").strip()
    return None


def _apply_required_priority_when_mixed(
    scores: dict[str, float],
    *,
    explanation_matches: tuple[str, ...],
    confusion_matches: tuple[str, ...],
    candidate_answer: str | None,
) -> None:
    if explanation_matches and candidate_answer is not None:
        scores["explanation"] = max(scores["explanation"], 0.95)
        scores["evaluation"] = min(scores["evaluation"], scores["explanation"] - 0.05)
    if explanation_matches and confusion_matches:
        scores["explanation"] = max(scores["explanation"], 0.95)
        scores["confusion"] = min(scores["confusion"], scores["explanation"] - 0.05)
    if confusion_matches and candidate_answer is not None and not explanation_matches:
        scores["confusion"] = max(scores["confusion"], 0.9)
        scores["evaluation"] = min(scores["evaluation"], scores["confusion"] - 0.05)


def _select_highest_score(scores: dict[str, float]) -> IntentType:
    return max(
        INTENT_PRIORITY,
        key=lambda intent: (scores[intent], -INTENT_PRIORITY.index(intent)),
    )


def _selected_matches(
    selected: IntentType,
    *,
    explanation_matches: tuple[str, ...],
    confusion_matches: tuple[str, ...],
    evaluation_matches: tuple[str, ...],
    candidate_answer: str | None,
) -> tuple[str, ...]:
    if selected == "explanation":
        return explanation_matches
    if selected == "confusion":
        return confusion_matches
    if evaluation_matches:
        return evaluation_matches
    return ("candidate_answer",) if candidate_answer is not None else ()


def _urgency_for(intent_type: IntentType, confidence: float) -> Urgency:
    if intent_type == "confusion" and confidence >= 0.72:
        return "high"
    if intent_type == "evaluation" and confidence >= 0.7:
        return "normal"
    return "low" if confidence < 0.45 else "normal"


def _has_step_term(text: str) -> bool:
    return any(term in text for term in STEP_TERMS)


def _has_math_command(text: str) -> bool:
    return any(signal in text for signal in MATH_COMMAND_SIGNALS)


def _looks_like_answer_only(text: str) -> bool:
    return _extract_candidate_answer(text) is not None or len(text.split()) <= 3


def _normalize_text(raw_input: str) -> str:
    return " ".join(raw_input.lower().strip().split())


def _matched_signals(text: str, signals: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(signal for signal in signals if signal in text)
