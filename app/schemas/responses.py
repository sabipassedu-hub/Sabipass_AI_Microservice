from typing import Literal, Optional

from pydantic import BaseModel


class CanvasDirective(BaseModel):
    render_type: Literal["interactive_quiz_game", "split_view_doc", "step_by_step_solution"]
    canvas_meta: dict
    payload_data: list


class MicroRewards(BaseModel):
    trigger_animation: Optional[str]
    praise_type: Optional[str]
    xp_boost_awarded: int


class NeuralSyncPayload(BaseModel):
    updated_bkt_mastery: float
    calculated_learning_velocity: float
    updated_weakness_array: list[str]


class SabiNeuralResponse(BaseModel):
    tutor_conversational_text: str
    canvas_directive: Optional[CanvasDirective]
    micro_rewards: Optional[MicroRewards]
    neural_sync_payload: NeuralSyncPayload
