"""
FastAPI application entrypoint.

Run with:
    uvicorn app.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.database.db import init_db
from app.api.routes import router
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

app = FastAPI(
    title="AI-First CRM HCP Module API",
    description="Log Interaction Screen backend — manual form + LangGraph AI assistant",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.on_event("startup")
def on_startup() -> None:
    logger.info("Starting up — initializing database tables (app_env=%s)", settings.app_env)
    init_db()


@app.get("/")
def health_check():
    return {"status": "ok", "service": "hcp-crm-backend"}
