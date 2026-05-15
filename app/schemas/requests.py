from pydantic import BaseModel


class RequestMetadata(BaseModel):
    transaction_id: str
    timestamp: str
    client_latency_ms: int


class StudentIdentity(BaseModel):
    student_id: str
    subscription_tier: str
    academic_stage: str
    target_examination: str


class CognitiveAptitudeProfile(BaseModel):
    learning_velocity_index: float
    scaffolding_dependency: str
    complexity_tolerance: str
    retention_decay_rate: str


class EmotionalTelemetry(BaseModel):
    detected_frustration_signals: list[str]
    session_sentiment_trend: str
    focus_integrity_score: float


class CurrentInteractionContext(BaseModel):
    user_input_text: str
    active_topic_node: str
    previous_bot_response_id: str
    attempt_count_on_current_concept: int


class HistoricalMasteryMap(BaseModel):
    known_weaknesses: list[str]
    mastered_strengths: list[str]


class NeuralChatRequest(BaseModel):
    request_metadata: RequestMetadata
    student_identity: StudentIdentity
    cognitive_aptitude_profile: CognitiveAptitudeProfile
    emotional_telemetry: EmotionalTelemetry
    current_interaction_context: CurrentInteractionContext
    historical_mastery_map: HistoricalMasteryMap
