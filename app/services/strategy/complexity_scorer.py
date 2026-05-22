"""Layer 2 complexity scoring.

Purpose: compute a local 0-5 complexity score from attempts, frustration,
trend, intent, and math-symbol signals. Constraints: fully deterministic,
no network calls, no model calls, and safe handling of Nigerian Pidgin
signals.
"""

from collections.abc import Sequence
from dataclasses import dataclass


ADVANCED_TOPIC_TERMS = {
    "bearing",
    "bearings",
    "cosine",
    "differentiation",
    "factor",
    "factors",
    "gradient",
    "integration",
    "log",
    "logarithm",
    "quadratic",
    "root",
    "roots",
    "sine",
    "surd",
    "tangent",
    "trigonometry",
}
NEGATIVE_TRENDS = {"declining", "negative", "worsening", "frustrated"}
PIDGIN_CONFUSION_TERMS = {
    "abeg",
    "i no understand",
    "no understand",
    "wahala",
    "show me step",
}
SCAFFOLDING_WEIGHTS = {"medium": 0, "high": 1}
INTENT_WEIGHTS = {
    "explanation": 1,
    "confusion": 1,
    "evaluation": 0,
}


@dataclass(frozen=True)
class ComplexitySignals:
    """Local signals used before strategy compilation."""

    raw_input: str
    errors_on_same_concept_space: int = 0
    detected_frustration_signals: Sequence[str] = ()
    rage_clicks: Sequence[str] = ()
    caps_lock_aggression: Sequence[str] = ()
    sentiment_trends: str = "stable"
    scaffolding_flag: str = "low"
    complexity_tolerance: str = "medium"
    intent: str | None = None


def score_complexity(signals: ComplexitySignals) -> int:
    """Score request complexity for strategy compilation."""
    text = _normalize_text(signals.raw_input)
    if not text:
        return 0

    score = _score_input_text(text)
    score += _score_learning_signals(signals)
    score += _score_emotional_signals(text, signals)
    score += SCAFFOLDING_WEIGHTS.get(signals.scaffolding_flag.lower(), 0)
    score += INTENT_WEIGHTS.get((signals.intent or "").lower(), 0)

    if signals.complexity_tolerance.lower() == "low":
        score += 1
    elif signals.complexity_tolerance.lower() == "high":
        score -= 1

    return max(0, min(5, score))


def _normalize_text(raw_input: str) -> str:
    return " ".join(raw_input.lower().split())


def _score_input_text(text: str) -> int:
    score = 1
    word_count = len(text.split())

    if word_count >= 16:
        score += 1
    if word_count >= 32:
        score += 1
    if _has_equation_or_advanced_symbol(text):
        score += 1
    if any(term in text for term in ADVANCED_TOPIC_TERMS):
        score += 1

    return score


def _has_equation_or_advanced_symbol(text: str) -> bool:
    words = set(text.replace(".", " ").replace(",", " ").split())
    has_variable_equation = "=" in text and any(variable in text for variable in ("x", "y", "z"))
    has_advanced_symbol = "^" in text or bool({"sqrt", "sin", "cos", "tan"} & words)
    return has_variable_equation or has_advanced_symbol


def _score_learning_signals(signals: ComplexitySignals) -> int:
    attempts = max(0, signals.errors_on_same_concept_space)

    if attempts >= 4:
        return 2
    if attempts >= 2:
        return 1
    return 0


def _score_emotional_signals(text: str, signals: ComplexitySignals) -> int:
    score = 0
    frustration_count = len(signals.detected_frustration_signals)

    if frustration_count >= 2:
        score += 2
    elif frustration_count == 1:
        score += 1

    if signals.rage_clicks or signals.caps_lock_aggression:
        score += 1
    if signals.sentiment_trends.lower() in NEGATIVE_TRENDS:
        score += 1
    if any(term in text for term in PIDGIN_CONFUSION_TERMS):
        score += 1

    return score
