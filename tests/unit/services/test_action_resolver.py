from types import SimpleNamespace

from app.services.action_resolver import resolve_tutor_action
from app.services.strategy.intent_parser import parse_intent


def state(phase: str = "evaluation", attempt: int = 1, correct_pattern=None):
    return SimpleNamespace(
        phase=phase,
        attempt=attempt,
        current_question_id="q-linear-001",
        correct_pattern=correct_pattern or [],
    )


def test_explanation_in_evaluation_resolves_to_step_only_without_mutation():
    intent = parse_intent(
        "why are we subtracting 4",
        session_state=state("evaluation"),
    )

    action = resolve_tutor_action(intent=intent, learning_state=state("evaluation"))

    assert action.action_type == "explain_step"
    assert action.state_mutation_allowed is False
    assert action.next_phase == "evaluation"
    assert action.progression_recommendation == "continue_current_phase"


def test_evaluation_intent_resolves_to_grade_answer():
    intent = parse_intent("x = 3", session_state=state("evaluation"))

    action = resolve_tutor_action(intent=intent, learning_state=state("evaluation"))

    assert action.action_type == "grade_answer"
    assert action.state_mutation_allowed is True
    assert action.state_effect == "grade_candidate_answer"


def test_attempt_four_resolves_to_intervention():
    intent = parse_intent("x = 3", session_state=state("practice", attempt=4))

    action = resolve_tutor_action(intent=intent, learning_state=state("practice", attempt=4))

    assert action.action_type == "intervention"
    assert action.progression_recommendation == "intervention_required"
