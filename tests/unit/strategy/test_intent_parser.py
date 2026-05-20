from app.services.strategy.intent_parser import IntentResult, parse_intent


def test_parse_explanation_intent_from_english_question():
    result = parse_intent("Why did the sign change when solving the equation?")

    assert result == IntentResult(
        intent_type="explanation",
        urgency="normal",
        matched_signals=("why",),
    )


def test_parse_pidgin_explanation_signal():
    result = parse_intent("Abeg make I understand how e dey work for surds.")

    assert result.intent_type == "explanation"
    assert result.urgency == "normal"
    assert "make i understand" in result.matched_signals


def test_parse_correction_intent_before_explanation():
    result = parse_intent("This is wrong, how did you get x = 4?")

    assert result.intent_type == "correction"
    assert result.urgency == "high"
    assert "this is wrong" in result.matched_signals


def test_parse_answer_request_intent():
    result = parse_intent("Just tell me the answer for number 5.")

    assert result.intent_type == "answer_request"
    assert result.urgency == "normal"
    assert "just tell me" in result.matched_signals


def test_parse_escape_valve_for_frustrated_direct_answer_request():
    result = parse_intent("I don tire, abeg just give me the answer.")

    assert result.intent_type == "escape_valve"
    assert result.urgency == "high"
    assert "i don tire" in result.matched_signals


def test_parse_defaults_to_practice_when_no_signal_matches():
    result = parse_intent("Solve 3x + 1 = 10.")

    assert result == IntentResult(
        intent_type="practice",
        urgency="low",
        matched_signals=(),
    )
