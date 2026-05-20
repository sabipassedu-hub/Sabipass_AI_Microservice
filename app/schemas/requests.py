from typing import Literal, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.config import get_history_turn_limit


AppExecutionMode = Literal["exam_prep", "curriculum_coach", "general_prompt", "navigation_click"]
AnswerOption = Literal["A", "B", "C", "D"]
Tier = Literal["free", "premium"]


class RequestMetadata(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    uuid_transaction_id: str = Field(
        validation_alias=AliasChoices("uuid_transaction_id", "transaction_id")
    )
    timestamp: str
    device_latency_ms: int = Field(
        validation_alias=AliasChoices("device_latency_ms", "client_latency_ms")
    )

    @property
    def transaction_id(self) -> str:
        return self.uuid_transaction_id

    @property
    def client_latency_ms(self) -> int:
        return self.device_latency_ms


class StudentIdentity(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    student_db_id: str = Field(validation_alias=AliasChoices("student_db_id", "student_id"))
    tier: Tier = Field(default="free", validation_alias=AliasChoices("tier", "subscription_tier"))
    academic_scope: str = Field(
        default="general",
        validation_alias=AliasChoices("academic_scope", "academic_stage"),
    )
    exam_target: str = Field(
        default="WAEC",
        validation_alias=AliasChoices("exam_target", "target_examination"),
    )

    @field_validator("tier", mode="before")
    @classmethod
    def normalize_tier(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @property
    def student_id(self) -> str:
        return self.student_db_id

    @property
    def subscription_tier(self) -> str:
        return self.tier

    @property
    def academic_stage(self) -> str:
        return self.academic_scope

    @property
    def target_examination(self) -> str:
        return self.exam_target


class CognitiveAptitudeProfile(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    regression_slope: float = Field(
        default=0.0,
        validation_alias=AliasChoices("regression_slope", "learning_velocity_index"),
    )
    scaffolding_flag: str = Field(
        default="low",
        validation_alias=AliasChoices("scaffolding_flag", "scaffolding_dependency"),
    )
    complexity_tolerance: str = "medium"
    knowledge_decay_params: str = Field(
        default="medium",
        validation_alias=AliasChoices("knowledge_decay_params", "retention_decay_rate"),
    )

    @property
    def learning_velocity_index(self) -> float:
        return self.regression_slope

    @property
    def scaffolding_dependency(self) -> str:
        return self.scaffolding_flag

    @property
    def retention_decay_rate(self) -> str:
        return self.knowledge_decay_params


class EmotionalTelemetry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    rage_clicks: list[str] = Field(default_factory=list)
    caps_lock_aggression: list[str] = Field(default_factory=list)
    detected_frustration_signals: list[str] = Field(default_factory=list)
    sentiment_trends: str = Field(
        default="stable",
        validation_alias=AliasChoices("sentiment_trends", "session_sentiment_trend"),
    )
    latency_focus_integrity: float = Field(
        default=1.0,
        validation_alias=AliasChoices("latency_focus_integrity", "focus_integrity_score"),
    )

    @property
    def session_sentiment_trend(self) -> str:
        return self.sentiment_trends

    @property
    def focus_integrity_score(self) -> float:
        return self.latency_focus_integrity


class CurrentInteractionContext(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    raw_whiteboard_input: str = Field(
        validation_alias=AliasChoices("raw_whiteboard_input", "user_input_text")
    )
    topic_node: str = Field(default="", validation_alias=AliasChoices("topic_node", "active_topic_node"))
    history_tokens: list[str] = Field(default_factory=list)
    errors_on_same_concept_space: int = Field(
        default=0,
        validation_alias=AliasChoices(
            "errors_on_same_concept_space",
            "attempt_count_on_current_concept",
        ),
    )
    previous_bot_response_id: Optional[str] = None
    correct_answer: Optional[AnswerOption] = None

    @property
    def user_input_text(self) -> str:
        return self.raw_whiteboard_input

    @property
    def active_topic_node(self) -> str:
        return self.topic_node

    @property
    def attempt_count_on_current_concept(self) -> int:
        return self.errors_on_same_concept_space


class HistoricalMasteryMap(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    active_weakness_arrays: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("active_weakness_arrays", "known_weaknesses"),
    )
    passed_topics_arrays: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("passed_topics_arrays", "mastered_strengths"),
    )

    @property
    def known_weaknesses(self) -> list[str]:
        return self.active_weakness_arrays

    @property
    def mastered_strengths(self) -> list[str]:
        return self.passed_topics_arrays


class NeuralChatRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    request_metadata: RequestMetadata
    student_identity: StudentIdentity
    efficiency_mode: bool = Field(
        default=False,
        validation_alias=AliasChoices("efficiency_mode", "efficiency_mode_enabled"),
    )
    app_execution_mode: AppExecutionMode = "general_prompt"
    cognitive_aptitude_profile: CognitiveAptitudeProfile
    emotional_telemetry: EmotionalTelemetry
    current_interaction_context: CurrentInteractionContext
    historical_mastery_map: HistoricalMasteryMap

    @model_validator(mode="after")
    def enforce_request_contract(self) -> "NeuralChatRequest":
        self._validate_correct_answer_scope()
        self._apply_history_limit()
        return self

    def _validate_correct_answer_scope(self) -> None:
        if self.current_interaction_context.correct_answer is None:
            return

        if self.app_execution_mode != "exam_prep":
            raise ValueError("correct_answer is allowed only when app_execution_mode is exam_prep")

        selected_option = self.current_interaction_context.raw_whiteboard_input.strip().upper()
        if selected_option not in {"A", "B", "C", "D"}:
            raise ValueError("correct_answer is allowed only for selected A-D exam options")

    def _apply_history_limit(self) -> None:
        max_history_turns = get_history_turn_limit(
            self.student_identity.tier,
            self.efficiency_mode,
        )

        if max_history_turns == 0:
            self.current_interaction_context.history_tokens = []
            return

        self.current_interaction_context.history_tokens = (
            self.current_interaction_context.history_tokens[-max_history_turns:]
        )
