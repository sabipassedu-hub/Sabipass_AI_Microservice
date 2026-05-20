from fastapi import FastAPI

from app.api.v1.routes.neural_chat import router as neural_chat_router
from app.core.lifespan import lifespan


app = FastAPI(lifespan=lifespan)
app.include_router(neural_chat_router)
