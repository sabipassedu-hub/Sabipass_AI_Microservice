from types import SimpleNamespace

from app.services.strategy.intent_parser import parse_intent


def active_state(phase: str = "evaluation"):
    return SimpleNamespace(phase=phase, current_question_id="q-linear-001")


def test_parse_explanation_intent_from_english_question():
    result = parse_intent(
        "Why did the sign change when solving the equation?",
        session_state=active_state(),
    )

    assert result.intent_type == "explanation"
    assert result.urgency == "normal"
    assert result.intent_scores["explanation"] >= 0.9
    assert "why" in result.matched_signals


def test_parse_pidgin_explanation_signal():
    result = parse_intent(
        "Abeg make I understand how e dey work for surds.",
        session_state=active_state("practice"),
    )

    assert result.intent_type == "explanation"
    assert "make i understand" in result.matched_signals


def test_mixed_answer_and_question_keeps_explanation_priority_and_stores_candidate():
    result = parse_intent(
        "I think it's 8 but why did the 4 disappear?",
        session_state=active_state(),
    )

    assert result.intent_type == "explanation"
    assert result.candidate_answer == "8"
    assert result.intent_scores["explanation"] > result.intent_scores["evaluation"]


def test_confusion_beats_evaluation_when_student_is_stuck_with_candidate():
    result = parse_intent(
        "I'm stuck, I think x = 8",
        session_state=active_state("practice"),
    )

    assert result.intent_type == "confusion"
    assert result.candidate_answer == "8"
    assert result.intent_scores["confusion"] > result.intent_scores["evaluation"]


def test_parse_evaluation_intent_from_answer_structure():
    result = parse_intent("x = 3", session_state=active_state())

    assert result.intent_type == "evaluation"
    assert result.candidate_answer == "3"
    assert result.intent_scores["evaluation"] >= 0.7


def test_low_signal_active_question_defaults_to_confusion_not_grading():
    result = parse_intent("hmm", session_state=active_state("practice"))

    assert result.intent_type == "confusion"
    assert result.candidate_answer is None
