from dataclasses import FrozenInstanceError

import pytest

from app.schemas.strategy import ModelStrategy, PedagogyStrategy, RagStrategy, StateStrategy


def build_strategy(**overrides) -> StateStrategy:
    strategy_data = {
        "execution_path": "single_pass",
        "complexity_score": 2,
        "normalized_concept": "linear_equations",
        "normalization_confidence": 0.95,
        "normalization_status": "strict",
        "rag_strategy": RagStrategy(
            mode="precision",
            target_collection="exam_bank",
            query_concept_key="linear_equations",
            filters=(
                ("subject", "mathematics"),
                ("topic", "linear_equations"),
            ),
            top_k=3,
        ),
        "pedagogy_strategy": PedagogyStrategy(
            teaching_mode="direct_instruction",
            response_format="text_only",
            intent_type="explanation",
            urgency="normal",
        ),
        "model_strategy": ModelStrategy(
            tier="free",
            efficiency_mode=False,
            execution_path="single_pass",
        ),
    }
    strategy_data.update(overrides)
    return StateStrategy(**strategy_data)


def test_state_strategy_is_immutable():
    strategy = build_strategy()

    with pytest.raises(FrozenInstanceError):
        strategy.complexity_score = 5

    with pytest.raises(FrozenInstanceError):
        strategy.rag_strategy.top_k = 5


def test_state_strategy_validates_score_and_confidence_ranges():
    with pytest.raises(ValueError, match="complexity_score"):
        build_strategy(complexity_score=6)

    with pytest.raises(ValueError, match="normalization_confidence"):
        build_strategy(normalization_confidence=1.5)


def test_rag_strategy_filters_are_tuple_based_and_bounded():
    strategy = build_strategy()

    assert strategy.rag_strategy.filters == (
        ("subject", "mathematics"),
        ("topic", "linear_equations"),
    )
    assert strategy.rag_strategy.filter_dict == {
        "subject": "mathematics",
        "topic": "linear_equations",
    }

    with pytest.raises(ValueError, match="top_k"):
        RagStrategy(
            mode="precision",
            target_collection="exam_bank",
            query_concept_key="linear_equations",
            filters=(),
            top_k=6,
        )
