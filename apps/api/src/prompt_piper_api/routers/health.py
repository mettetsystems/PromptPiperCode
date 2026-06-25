"""Health check endpoint."""

from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel, Field

from prompt_piper_api import __version__
from prompt_piper_api.config import get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str = Field(examples=["ok"])
    service: str
    version: str
    environment: str
    database: str
    timestamp: datetime


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Return service health and runtime metadata."""
    settings = get_settings()
    database_kind = "sqlite" if settings.is_sqlite else "postgresql"

    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=__version__,
        environment=settings.app_env,
        database=database_kind,
        timestamp=datetime.now(UTC),
    )
