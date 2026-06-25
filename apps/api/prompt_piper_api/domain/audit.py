from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class AuditEventKind(StrEnum):
    """Categories of locally audited actions."""

    EXTERNAL_INFERENCE = "external_inference"
    REGISTRY_FINALIZE = "registry_finalize"
    ARTIFACT_EXPORT = "artifact_export"


class AuditOutcome(StrEnum):
    BLOCKED = "blocked"
    SUCCESS = "success"
    ERROR = "error"


class AuditEvent(BaseModel):
    """Append-only local audit record (metadata only — no prompt bodies)."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    kind: AuditEventKind
    outcome: AuditOutcome
    session_id: str | None = None
    prompt_id: str | None = None
    version: int | None = Field(default=None, ge=1)
    action: str | None = None
    block_reason: str | None = None
    provider: str | None = None
    model: str | None = None
    explicit_approval: bool | None = None
    artifact_location: str | None = None
    error_code: str | None = None
    message: str | None = None
