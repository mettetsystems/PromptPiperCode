from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from prompt_piper_api.domain.enums import SessionState
from prompt_piper_api.domain.requirement_card import RequirementCard


def utc_now() -> datetime:
    return datetime.now(tz=UTC)


class PromptSession(BaseModel):
    """A single prompt design workflow from intake through export."""

    id: UUID = Field(default_factory=uuid4)
    title: str = Field(default="Untitled session")
    state: SessionState = Field(default=SessionState.INTAKE)
    requirement_card: RequirementCard = Field(default_factory=RequirementCard)
    current_draft_id: UUID | None = Field(
        default=None,
        description="ID of the draft currently being edited or reviewed.",
    )
    prompt_id: str | None = Field(
        default=None,
        description="Stable registry identifier assigned at finalization.",
    )
    template_source_session_id: UUID | None = Field(
        default=None,
        description="When set, this session was created from a completed template session.",
    )
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    def touch(self) -> None:
        """Refresh updated_at after a mutation."""
        self.updated_at = utc_now()
