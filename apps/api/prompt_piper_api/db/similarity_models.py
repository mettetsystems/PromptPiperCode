from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(tz=UTC)


class SimilarityDocumentRow(SQLModel, table=True):
    """Indexed retrievable document for hybrid similarity search."""

    __tablename__ = "similarity_documents"

    id: int | None = Field(default=None, primary_key=True)
    prompt_id: str = Field(index=True)
    version: int = Field(ge=1)
    title: str = ""
    document_kind: str = Field(index=True)
    text: str
    embedding_json: str
    artifact_paths_json: str = "{}"
    created_at: datetime = Field(default_factory=utc_now)
