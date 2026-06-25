from enum import StrEnum

from pydantic import BaseModel, Field


class DocumentKind(StrEnum):
    """Retrievable document slices indexed per finalized prompt."""

    CANONICAL = "canonical"
    ABSTRACT = "abstract"
    LESSONS_LEARNED = "lessons_learned"


class SimilarityMatch(BaseModel):
    prompt_id: str
    title: str
    similarity_score: float = Field(ge=0.0, le=1.0)
    artifact_paths: dict[str, str] = Field(default_factory=dict)
    delta: str = ""
    document_kind: DocumentKind | None = None


class SimilarityCheckResult(BaseModel):
    warning: str | None = None
    matches: list[SimilarityMatch] = Field(default_factory=list)


SIMILARITY_WARNING_MESSAGE = "A similar prompt pattern may already exist."
