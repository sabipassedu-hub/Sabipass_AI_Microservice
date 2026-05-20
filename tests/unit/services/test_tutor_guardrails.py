from tests.unit.services.test_tutor_engine import build_request
from app.services.bkt_engine import calculate_student_mastery


def test_bkt_adapter_uses_request_signals_instead_of_fixed_placeholder():
    strong_request = build_request(raw_whiteboard_input="Explain linear equations")
    weak_request = build_request(raw_whiteboard_input="Explain linear equations")
    weak_request.current_interaction_context.errors_on_same_concept_space = 3
    weak_request.cognitive_aptitude_profile.scaffolding_flag = "high"

    strong = calculate_student_mastery(strong_request)
    weak = calculate_student_mastery(weak_request)

    assert strong["updated_bkt_mastery"] > weak["updated_bkt_mastery"]
    assert strong["calculated_learning_velocity"] == 0.2
