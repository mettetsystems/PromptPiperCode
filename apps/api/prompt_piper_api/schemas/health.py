from datetime import UTC, datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(examples=["ok"])
    service: str = Field(examples=["prompt-piper-api"])
    version: str
    timestamp: datetime
    database: str = Field(description="Connected database backend (sqlite or postgresql)")


class LlmHealthResponse(BaseModel):
    """Live probe of the configured local OpenAI-compatible model server."""

    llm_enabled: bool
    status: str = Field(
        description="ok | disabled | unreachable",
        examples=["ok"],
    )
    endpoint: str | None = None
    model_name: str | None = None
    message: str
    checked_at: datetime


def utc_now() -> datetime:
    return datetime.now(tz=UTC)
