import re
from datetime import datetime
from typing import Literal, Optional

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)

from app.core.config import get_history_turn_limit


AppExecutionMode = Literal[
    "exam_prep",
    "curriculum_coach",
    "homework_explainer",
    "general_prompt",
    "navigation_click",
]
AnswerOption = Literal["A", "B", "C", "D"]
Tier = Literal["free", "premium"]
SignalLevel = Literal["low", "medium", "high"]
LearningPhase = Literal[
    "explanation",
    "guided_example",
    "practice",
    "evaluation",
    "intervention",
]
DifficultyLevel = Literal["easy", "medium", "hard"]
ConfidenceLevel = Literal["low", "medium", "high"]
SentimentTrend = Literal[
    "stable",
    "improving",
    "positive",
    "declining",
    "negative",
    "worsening",
    "frustrated",
]

MAX_ID_LENGTH = 128
MAX_TIMESTAMP_LENGTH = 64
MAX_DEVICE_LATENCY_MS = 300_000
MAX_RAW_WHITEBOARD_INPUT_LENGTH = 4_000
MAX_TOPIC_NODE_LENGTH = 128
MAX_HISTORY_TOKENS = 50
MAX_HISTORY_TOKEN_LENGTH = 1_000
MAX_MASTERY_ITEMS = 50
MAX_MASTERY_ITEM_LENGTH = 128
MAX_STATE_ID_LENGTH = 128
MAX_QUESTION_HISTORY_ITEMS = 20
MAX_TELEMETRY_EVENTS = 50
MAX_TELEMETRY_EVENT_LENGTH = 128
MAX_SHORT_SIGNAL_LENGTH = 64
MAX_CONCEPT_ATTEMPTS = 100
MAX_HINTS_USED = 20
MAX_STREAK = 20
MAX_RESPONSE_TIME_MS = 3_600_000

_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


def _normalize_bounded_string(
    value: object,
    field_name: str,
    max_length: int,
    *,
    allow_empty: bool = False,
    lowercase: bool = False,
    uppercase: bool = False,
) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")

    normalized = value.strip()
    if not normalized and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    if len(normalized) > max_length:
        raise ValueError(f"{field_name} must be at most {max_length} characters")
    if lowercase:
        return normalized.lower()
    if uppercase:
        return normalized.upper()
    return normalized


def _normalize_id(value: object, field_name: str) -> str:
    normalized = _normalize_bounded_string(value, field_name, MAX_ID_LENGTH)
    if _ID_PATTERN.fullmatch(normalized) is None:
        raise ValueError(f"{field_name} contains unsupported characters")
    return normalized


def _normalize_optional_id(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _normalize_id(value, field_name)


def _normalize_iso_timestamp(value: object) -> str:
    normalized = _normalize_bounded_string(value, "timestamp", MAX_TIMESTAMP_LENGTH)
    if "T" not in normalized:
        raise ValueError("timestamp must use ISO-8601 date-time format")

    parseable = normalized[:-1] + "+00:00" if normalized.endswith("Z") else normalized
    try:
        parsed = datetime.fromisoformat(parseable)
    except ValueError as exc:
        raise ValueError("timestamp must use ISO-8601 date-time format") from exc

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include timezone information")
    return normalized


def _normalize_string_list(
    value: object,
    field_name: str,
    *,
    max_items: int,
    max_item_length: int,
    lowercase: bool = False,
) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    if len(value) > max_items:
        raise ValueError(f"{field_name} must contain at most {max_items} items")

    normalized_items = []
    for item in value:
        normalized_items.append(
            _normalize_bounded_string(
                item,
                field_name,
                max_item_length,
                lowercase=lowercase,
            )
        )
    return normalized_items


class RequestMetadata(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    uuid_transaction_id: str = Field(
        min_length=1,
        max_length=MAX_ID_LENGTH,
        validation_alias=AliasChoices("uuid_transaction_id", "transaction_id")
    )
    timestamp: str = Field(min_length=1, max_length=MAX_TIMESTAMP_LENGTH)
    device_latency_ms: int = Field(
        ge=0,
        le=MAX_DEVICE_LATENCY_MS,
        validation_alias=AliasChoices("device_latency_ms", "client_latency_ms")
    )

    @field_validator("uuid_transaction_id", mode="before")
    @classmethod
    def normalize_transaction_id(cls, value: object) -> str:
        return _normalize_id(value, "uuid_transaction_id")

    @field_validator("timestamp", mode="before")
    @classmethod
    def normalize_timestamp(cls, value: object) -> str:
        return _normalize_iso_timestamp(value)

    @property
    def transaction_id(self) -> str:
        return self.uuid_transaction_id

    @property
    def client_latency_ms(self) -> int:
        return self.device_latency_ms


class StudentIdentity(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    student_db_id: str = Field(
        min_length=1,
        max_length=MAX_ID_LENGTH,
        validation_alias=AliasChoices("student_db_id", "student_id"),
    )
    tier: Tier = Field(
        default="free",
        validation_alias=AliasChoices("tier", "subscription_tier"),
    )
    academic_scope: str = Field(
        default="general",
        min_length=1,
        max_length=MAX_SHORT_SIGNAL_LENGTH,
        validation_alias=AliasChoices("academic_scope", "academic_stage"),
    )
    exam_target: str = Field(
        default="WAEC",
        min_length=1,
        max_length=MAX_SHORT_SIGNAL_LENGTH,
        validation_alias=AliasChoices("exam_target", "target_examination"),
    )

    @field_validator("student_db_id", mode="before")
    @classmethod
    def normalize_student_id(cls, value: object) -> str:
        return _normalize_id(value, "student_db_id")

    @field_validator("tier", mode="before")
    @classmethod
    def normalize_tier(cls, value: object) -> str:
        return _normalize_bounded_string(value, "tier", MAX_SHORT_SIGNAL_LENGTH, lowercase=True)

    @field_validator("academic_scope", mode="before")
    @classmethod
    def normalize_academic_scope(cls, value: object) -> str:
        return _normalize_bounded_string(
            value,
            "academic_scope",
            MAX_SHORT_SIGNAL_LENGTH,
            lowercase=True,
        )

    @field_validator("exam_target", mode="before")
    @classmethod
    def normalize_exam_target(cls, value: object) -> str:
        return _normalize_bounded_string(
            value,
            "exam_target",
            MAX_SHORT_SIGNAL_LENGTH,
            uppercase=True,
        )

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
        ge=-10.0,
        le=10.0,
        validation_alias=AliasChoices("regression_slope", "learning_velocity_index"),
    )
    scaffolding_flag: SignalLevel = Field(
        default="low",
        validation_alias=AliasChoices("scaffolding_flag", "scaffolding_dependency"),
    )
    complexity_tolerance: SignalLevel = "medium"
    knowledge_decay_params: SignalLevel = Field(
        default="medium",
        validation_alias=AliasChoices("knowledge_decay_params", "retention_decay_rate"),
    )

    @field_validator(
        "scaffolding_flag",
        "complexity_tolerance",
        "knowledge_decay_params",
        mode="before",
    )
    @classmethod
    def normalize_signal_level(cls, value: object, info: ValidationInfo) -> str:
        return _normalize_bounded_string(
            value,
            info.field_name,
            MAX_SHORT_SIGNAL_LENGTH,
            lowercase=True,
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

    rage_clicks: list[str] = Field(
        default_factory=list,
        max_length=MAX_TELEMETRY_EVENTS,
    )
    caps_lock_aggression: list[str] = Field(
        default_factory=list,
        max_length=MAX_TELEMETRY_EVENTS,
    )
    detected_frustration_signals: list[str] = Field(
        default_factory=list,
        max_length=MAX_TELEMETRY_EVENTS,
    )
    sentiment_trends: SentimentTrend = Field(
        default="stable",
        validation_alias=AliasChoices("sentiment_trends", "session_sentiment_trend"),
    )
    latency_focus_integrity: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        validation_alias=AliasChoices("latency_focus_integrity", "focus_integrity_score"),
    )

    @field_validator(
        "rage_clicks",
        "caps_lock_aggression",
        "detected_frustration_signals",
        mode="before",
    )
    @classmethod
    def normalize_telemetry_events(cls, value: object, info: ValidationInfo) -> list[str]:
        return _normalize_string_list(
            value,
            info.field_name,
            max_items=MAX_TELEMETRY_EVENTS,
            max_item_length=MAX_TELEMETRY_EVENT_LENGTH,
            lowercase=True,
        )

    @field_validator("sentiment_trends", mode="before")
    @classmethod
    def normalize_sentiment_trend(cls, value: object) -> str:
        return _normalize_bounded_string(
            value,
            "sentiment_trends",
            MAX_SHORT_SIGNAL_LENGTH,
            lowercase=True,
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
        min_length=1,
        max_length=MAX_RAW_WHITEBOARD_INPUT_LENGTH,
        validation_alias=AliasChoices("raw_whiteboard_input", "user_input_text")
    )
    topic_node: str = Field(
        default="",
        max_length=MAX_TOPIC_NODE_LENGTH,
        validation_alias=AliasChoices("topic_node", "active_topic_node"),
    )
    history_tokens: list[str] = Field(
        default_factory=list,
        max_length=MAX_HISTORY_TOKENS,
    )
    errors_on_same_concept_space: int = Field(
        default=0,
        ge=0,
        le=MAX_CONCEPT_ATTEMPTS,
        validation_alias=AliasChoices(
            "errors_on_same_concept_space",
            "attempt_count_on_current_concept",
        ),
    )
    previous_bot_response_id: Optional[str] = Field(
        default=None,
        max_length=MAX_ID_LENGTH,
    )
    correct_answer: Optional[AnswerOption] = None

    @field_validator("raw_whiteboard_input", mode="before")
    @classmethod
    def normalize_raw_whiteboard_input(cls, value: object) -> str:
        return _normalize_bounded_string(
            value,
            "raw_whiteboard_input",
            MAX_RAW_WHITEBOARD_INPUT_LENGTH,
        )

    @field_validator("topic_node", mode="before")
    @classmethod
    def normalize_topic_node(cls, value: object) -> str:
        return _normalize_bounded_string(
            value,
            "topic_node",
            MAX_TOPIC_NODE_LENGTH,
            allow_empty=True,
            lowercase=True,
        )

    @field_validator("history_tokens", mode="before")
    @classmethod
    def normalize_history_tokens(cls, value: object) -> list[str]:
        return _normalize_string_list(
            value,
            "history_tokens",
            max_items=MAX_HISTORY_TOKENS,
            max_item_length=MAX_HISTORY_TOKEN_LENGTH,
        )

    @field_validator("previous_bot_response_id", mode="before")
    @classmethod
    def normalize_previous_bot_response_id(cls, value: object) -> str | None:
        return _normalize_optional_id(value, "previous_bot_response_id")

    @field_validator("correct_answer", mode="before")
    @classmethod
    def normalize_correct_answer(cls, value: object) -> str | None:
        if value is None:
            return None
        return _normalize_bounded_string(
            value,
            "correct_answer",
            1,
            uppercase=True,
        )

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
        max_length=MAX_MASTERY_ITEMS,
        validation_alias=AliasChoices("active_weakness_arrays", "known_weaknesses"),
    )
    passed_topics_arrays: list[str] = Field(
        default_factory=list,
        max_length=MAX_MASTERY_ITEMS,
        validation_alias=AliasChoices("passed_topics_arrays", "mastered_strengths"),
    )

    @field_validator("active_weakness_arrays", "passed_topics_arrays", mode="before")
    @classmethod
    def normalize_mastery_items(cls, value: object, info: ValidationInfo) -> list[str]:
        return _normalize_string_list(
            value,
            info.field_name,
            max_items=MAX_MASTERY_ITEMS,
            max_item_length=MAX_MASTERY_ITEM_LENGTH,
            lowercase=True,
        )

    @property
    def known_weaknesses(self) -> list[str]:
        return self.active_weakness_arrays

    @property
    def mastered_strengths(self) -> list[str]:
        return self.passed_topics_arrays


class LearningSessionState(BaseModel):
    """Persisted state-machine snapshot restored by Node for every tutoring turn."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    topic: str = Field(
        min_length=1,
        max_length=MAX_STATE_ID_LENGTH,
        validation_alias=AliasChoices("topic", "topic_id"),
    )
    subtopic: str = Field(
        min_length=1,
        max_length=MAX_STATE_ID_LENGTH,
        validation_alias=AliasChoices("subtopic", "subtopic_id"),
    )
    micro_skill: str = Field(
        min_length=1,
        max_length=MAX_STATE_ID_LENGTH,
        validation_alias=AliasChoices("micro_skill", "micro_skill_id"),
    )
    phase: LearningPhase = Field(
        validation_alias=AliasChoices("phase", "session_phase"),
    )
    attempt: int = Field(
        ge=0,
        le=MAX_CONCEPT_ATTEMPTS,
        validation_alias=AliasChoices("attempt", "attempt_number"),
    )
    streak: int = Field(
        ge=0,
        le=MAX_STREAK,
        validation_alias=AliasChoices("streak", "current_streak"),
    )
    mastery_score: float = Field(
        ge=0.0,
        le=1.0,
        validation_alias=AliasChoices("mastery_score", "mastery"),
    )
    state_version: int = Field(ge=1)
    current_question_id: Optional[str] = Field(default=None, max_length=MAX_ID_LENGTH)
    last_question_ids: list[str] = Field(
        default_factory=list,
        max_length=MAX_QUESTION_HISTORY_ITEMS,
    )
    correct_pattern: list[bool] = Field(
        default_factory=list,
        max_length=MAX_QUESTION_HISTORY_ITEMS,
    )
    response_time_ms: Optional[int] = Field(default=None, ge=0, le=MAX_RESPONSE_TIME_MS)
    confidence_level: Optional[ConfidenceLevel] = None
    hints_used: int = Field(default=0, ge=0, le=MAX_HINTS_USED)
    difficulty_level: DifficultyLevel = Field(
        default="easy",
        validation_alias=AliasChoices("difficulty_level", "difficulty"),
    )
    is_retention_check: bool = False

    @field_validator("topic", "subtopic", "micro_skill", mode="before")
    @classmethod
    def normalize_curriculum_key(cls, value: object, info: ValidationInfo) -> str:
        return _normalize_bounded_string(
            value,
            info.field_name,
            MAX_STATE_ID_LENGTH,
            lowercase=True,
        )

    @field_validator("current_question_id", mode="before")
    @classmethod
    def normalize_current_question_id(cls, value: object) -> str | None:
        return _normalize_optional_id(value, "current_question_id")

    @field_validator("last_question_ids", mode="before")
    @classmethod
    def normalize_last_question_ids(cls, value: object) -> list[str]:
        return _normalize_string_list(
            value,
            "last_question_ids",
            max_items=MAX_QUESTION_HISTORY_ITEMS,
            max_item_length=MAX_ID_LENGTH,
            lowercase=True,
        )

    @model_validator(mode="after")
    def enforce_state_machine_shape(self) -> "LearningSessionState":
        if self.phase == "evaluation" and self.attempt == 0:
            raise ValueError("evaluation phase requires attempt greater than 0")
        if len(self.correct_pattern) > len(self.last_question_ids):
            raise ValueError("correct_pattern cannot be longer than last_question_ids")
        return self


class NeuralChatRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

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
    learning_session_state: LearningSessionState

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
