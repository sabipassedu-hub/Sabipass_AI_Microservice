from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.neural_chat import router as neural_chat_router
from app.core.lifespan import lifespan


app = FastAPI(lifespan=lifespan)
app.include_router(health_router)
app.include_router(neural_chat_router)
FastAPIInstrumentor.instrument_app(app)
