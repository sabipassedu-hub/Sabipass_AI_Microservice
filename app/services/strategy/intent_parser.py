"""Layer 2 rule-based intent parser.

Purpose: classify explanation, correction, answer-request, and escape-valve
signals before pedagogy and model routing. Constraints: rule-based only,
Pidgin-aware, no ML dependency, and no final tutor text generation.
"""

from dataclasses import dataclass
from typing import Literal


IntentType = Literal["practice", "explanation", "correction", "answer_request", "escape_valve"]
Urgency = Literal["low", "normal", "high"]


CORRECTION_SIGNALS = (
    "this is wrong",
    "wrong answer",
    "you are wrong",
    "not correct",
    "e no correct",
    "na wrong",
)
ESCAPE_VALVE_SIGNALS = (
    "i don tire",
    "i am tired",
    "i'm tired",
    "i give up",
    "i no fit",
)
ANSWER_REQUEST_SIGNALS = (
    "just tell me",
    "give me the answer",
    "just give me",
    "answer only",
    "straight answer",
    "no explain",
)
EXPLANATION_SIGNALS = (
    "why",
    "how",
    "explain",
    "prove",
    "show me",
    "make i understand",
    "how e dey work",
    "wetin make",
    "abeg explain",
)


@dataclass(frozen=True)
class IntentResult:
    """Rule-based intent classification for strategy compilation."""

    intent_type: IntentType
    urgency: Urgency
    matched_signals: tuple[str, ...] = ()


def parse_intent(raw_input: str) -> IntentResult:
    """Parse request intent for strategy compilation."""
    text = _normalize_text(raw_input)
    if not text:
        return IntentResult(intent_type="practice", urgency="low")

    correction_matches = _matched_signals(text, CORRECTION_SIGNALS)
    if correction_matches:
        return IntentResult(
            intent_type="correction",
            urgency="high",
            matched_signals=correction_matches,
        )

    escape_matches = _matched_signals(text, ESCAPE_VALVE_SIGNALS)
    answer_matches = _matched_signals(text, ANSWER_REQUEST_SIGNALS)
    if escape_matches and answer_matches:
        return IntentResult(
            intent_type="escape_valve",
            urgency="high",
            matched_signals=escape_matches + answer_matches,
        )

    if answer_matches:
        return IntentResult(
            intent_type="answer_request",
            urgency="normal",
            matched_signals=answer_matches,
        )

    explanation_matches = _matched_signals(text, EXPLANATION_SIGNALS)
    if explanation_matches:
        return IntentResult(
            intent_type="explanation",
            urgency="normal",
            matched_signals=explanation_matches,
        )

    if escape_matches:
        return IntentResult(
            intent_type="escape_valve",
            urgency="high",
            matched_signals=escape_matches,
        )

    return IntentResult(intent_type="practice", urgency="low")


def _normalize_text(raw_input: str) -> str:
    return " ".join(raw_input.lower().strip().split())


def _matched_signals(text: str, signals: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(signal for signal in signals if signal in text)
