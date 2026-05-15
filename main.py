from fastapi import FastAPI

from app.schemas.requests import NeuralChatRequest
from app.schemas.responses import SabiNeuralResponse


app = FastAPI()


@app.post("/api/v1/neural/chat", response_model=SabiNeuralResponse)
def neural_chat(request: NeuralChatRequest):
    return {
        "tutor_conversational_text": "Let's solve it step by step.",
        "canvas_directive": {
            "render_type": "step_by_step_solution",
            "canvas_meta": {},
            "payload_data": [],
        },
        "micro_rewards": {
            "trigger_animation": None,
            "praise_type": None,
            "xp_boost_awarded": 0,
        },
        "neural_sync_payload": {
            "updated_bkt_mastery": 0.0,
            "calculated_learning_velocity": 0.0,
            "updated_weakness_array": [],
        },
    }
