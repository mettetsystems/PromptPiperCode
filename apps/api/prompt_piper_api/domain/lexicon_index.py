from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class LexiconEntrySource(StrEnum):
    WORDNET = "wordnet"
    GLOSSARY = "glossary"


class LexiconVectorRecord(BaseModel):
    """One searchable precision lexicon row."""

    id: str
    candidate: str
    pos: str
    source: LexiconEntrySource
    text: str
    embedding: list[float] = Field(default_factory=list)


class LexiconVectorIndexManifest(BaseModel):
    version: int = 1
    embedding_model: str
    entry_count: int = Field(ge=0)
    built_at: str
    entries: list[LexiconVectorRecord] = Field(default_factory=list)
