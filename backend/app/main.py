import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)
settings = get_settings()

masked_pw = settings.postgres_password[:4] + "****" if len(settings.postgres_password) > 4 else "****"
logger.info(
    "DB config: user=%s host=%s port=%s db=%s password=%s...",
    settings.postgres_user, settings.postgres_host, settings.postgres_port,
    settings.postgres_db, masked_pw,
)

from app.presentation.api.router import api_router

app = FastAPI(title="ClassFlow AI", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
