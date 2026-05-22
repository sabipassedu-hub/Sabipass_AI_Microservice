from app.services.strategy.complexity_scorer import ComplexitySignals, score_complexity


def test_simple_numeric_prompt_scores_low():
    signals = ComplexitySignals(raw_input="What is 2 + 3?")

    assert score_complexity(signals) == 1


def test_multi_step_math_with_learning_signals_scores_high():
    signals = ComplexitySignals(
        raw_input=(
            "I have tried three times. Solve x^2 - 5x + 6 = 0 "
            "and explain why the factors give the roots."
        ),
        errors_on_same_concept_space=3,
        detected_frustration_signals=("confused", "stuck"),
        sentiment_trends="declining",
        scaffolding_flag="high",
        complexity_tolerance="low",
        intent="explanation",
    )

    assert score_complexity(signals) == 5


def test_pidgin_confusion_and_step_request_increase_complexity():
    signals = ComplexitySignals(
        raw_input="Abeg I no understand this bearing wahala, show me step by step.",
        errors_on_same_concept_space=1,
        sentiment_trends="negative",
    )

    assert score_complexity(signals) == 4


def test_high_tolerance_keeps_stable_direct_answer_request_moderate():
    signals = ComplexitySignals(
        raw_input="Find x if 3x + 1 = 10.",
        intent="evaluation",
        complexity_tolerance="high",
    )

    assert score_complexity(signals) == 1
