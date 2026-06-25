from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from prompt_piper_api.domain.limits import MAX_DRAFT_BODY_CHARS


def utc_now() -> datetime:
    return datetime.now(tz=UTC)


class PromptDraft(BaseModel):
    """One versioned snapshot of prompt text within a session."""

    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    version: int = Field(ge=1, description="Monotonic version number within the session.")
    body: str = Field(
        default="",
        max_length=MAX_DRAFT_BODY_CHARS,
        description="Prompt text at this version.",
    )
    change_summary: str = Field(
        default="",
        description="Human-readable summary of what changed since the prior version.",
    )
    semantic_diff: str = Field(
        default="",
        description="Structured or narrative diff highlighting meaning-level changes.",
    )
    created_at: datetime = Field(default_factory=utc_now)
    is_canonical: bool = Field(
        default=False,
        description="Whether this draft is the session's canonical prompt text.",
    )
    is_frozen: bool = Field(
        default=False,
        description="Whether this draft is locked after registry finalization.",
    )

    @field_validator("version")
    @classmethod
    def version_must_be_positive(cls, value: int) -> int:
        if value < 1:
            msg = "Draft version must be >= 1"
            raise ValueError(msg)
        return value

    @classmethod
    def next_version(cls, existing_drafts: list["PromptDraft"]) -> int:
        """Return the next version number for a session's draft chain."""
        if not existing_drafts:
            return 1
        return max(draft.version for draft in existing_drafts) + 1

    @classmethod
    def create_revision(
        cls,
        *,
        session_id: UUID,
        existing_drafts: list["PromptDraft"],
        body: str,
        change_summary: str = "",
        semantic_diff: str = "",
        make_canonical: bool = False,
    ) -> "PromptDraft":
        """Create a new draft revision with an incremented version."""
        draft = cls(
            session_id=session_id,
            version=cls.next_version(existing_drafts),
            body=body,
            change_summary=change_summary,
            semantic_diff=semantic_diff,
            is_canonical=make_canonical,
        )
        if make_canonical:
            for existing in existing_drafts:
                existing.is_canonical = False
        return draft
