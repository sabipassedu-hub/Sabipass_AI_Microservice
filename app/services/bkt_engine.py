"""Stateless mastery signal adapter.

Node.js will eventually send attempt-level histories. Until then this module
turns the learning signals already present in the request into bounded mastery
and velocity values instead of returning fixed placeholders.
"""

from __future__ import annotations

from typing import Any


def calculate_student_mastery(payload: Any) -> dict[str, float | list[str]]:
    profile = payload.cognitive_aptitude_profile
    context = payload.current_interaction_context
    mastery_map = payload.historical_mastery_map

    velocity = _clamp(float(profile.regression_slope), -1.0, 1.0)
    mastery = 0.55 + (velocity * 0.15)
    mastery -= min(context.errors_on_same_concept_space, 5) * 0.07
    mastery -= len(mastery_map.active_weakness_arrays) * 0.02
    mastery += len(mastery_map.passed_topics_arrays) * 0.03

    if profile.scaffolding_flag == "high":
        mastery -= 0.08
    elif profile.scaffolding_flag == "low":
        mastery += 0.03

    return {
        "updated_bkt_mastery": round(_clamp(mastery, 0.05, 0.98), 3),
        "calculated_learning_velocity": round(velocity, 3),
        "updated_weakness_array": _updated_weaknesses(payload),
    }


def _updated_weaknesses(payload: Any) -> list[str]:
    weaknesses = list(payload.historical_mastery_map.active_weakness_arrays)
    topic = payload.current_interaction_context.topic_node
    if payload.current_interaction_context.errors_on_same_concept_space >= 2 and topic:
        weaknesses.append(topic)
    return sorted(set(weaknesses))


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))
