"""Layer 2 StateStrategy schema.

Purpose: define the immutable strategy object produced once after zero-pass and
consumed by RAG, math, tutor decision, and LLM layers. Constraints: downstream
layers may execute the strategy but must not mutate or reinterpret it.
"""

from dataclasses import dataclass
from typing import Any, Literal


ExecutionPath = Literal["single_pass", "two_pass"]
FilterValue = str | int | bool
NormalizationStatus = Literal["strict", "semantic", "degraded", "needs_clarification"]
RagMode = Literal["precision", "fallback", "none"]
ResponseFormat = Literal["text_only", "micro_clarification"]
TeachingMode = Literal[
    "socratic",
    "direct_instruction",
    "remediation",
    "direct_answer",
    "clarification",
    "guided_example",
    "practice",
    "evaluation",
    "system_intervention",
]
Urgency = Literal["low", "normal", "high"]


@dataclass(frozen=True)
class RagStrategy:
    """Retrieval plan produced by Layer 2; it does not execute retrieval."""

    mode: RagMode
    target_collection: str | None
    query_concept_key: str | None
    filters: tuple[tuple[str, FilterValue], ...]
    top_k: int

    def __post_init__(self) -> None:
        if not 0 <= self.top_k <= 5:
            raise ValueError("top_k must be between 0 and 5")

    @property
    def filter_dict(self) -> dict[str, FilterValue]:
        return dict(self.filters)


@dataclass(frozen=True)
class PedagogyStrategy:
    """Pedagogy hints for later tutor decisioning."""

    teaching_mode: TeachingMode
    response_format: ResponseFormat
    intent_type: str
    urgency: Urgency


@dataclass(frozen=True)
class ModelStrategy:
    """Model-routing hints without concrete provider or env-based model names."""

    tier: str
    efficiency_mode: bool
    execution_path: ExecutionPath


@dataclass(frozen=True)
class StateStrategy:
    """Immutable Layer 2 strategy snapshot for downstream execution."""

    execution_path: ExecutionPath
    complexity_score: int
    normalized_concept: str | None
    normalization_confidence: float
    normalization_status: NormalizationStatus
    rag_strategy: RagStrategy
    pedagogy_strategy: PedagogyStrategy
    model_strategy: ModelStrategy
    learning_state: Any | None = None
    state_control: dict[str, Any] | None = None
    action_plan: Any | None = None

    def __post_init__(self) -> None:
        if not 0 <= self.complexity_score <= 5:
            raise ValueError("complexity_score must be between 0 and 5")
        if not 0.0 <= self.normalization_confidence <= 1.0:
            raise ValueError("normalization_confidence must be between 0.0 and 1.0")
