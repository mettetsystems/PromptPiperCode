from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ExternalInferenceAuditOutcome(StrEnum):
    BLOCKED = "blocked"
    SUCCESS = "success"
    ERROR = "error"


class ExternalInferenceAuditEvent(BaseModel):
    """Local audit record for every external inference export attempt."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    session_id: str
    prompt_id: str | None = None
    version: int | None = Field(default=None, ge=1)
    outcome: ExternalInferenceAuditOutcome
    block_reason: str | None = None
    provider: str | None = None
    model: str | None = None
    explicit_approval: bool = False
    artifact_location: str | None = None
    inference_response_artifact_path: str | None = None
    error_message: str | None = None


class SendToInferenceResult(BaseModel):
    provider: str
    model: str
    prompt_id: str
    version: int = Field(ge=1)
    timestamp: datetime
    artifact_location: str
    inference_response_artifact_path: str
    response_text: str = ""
