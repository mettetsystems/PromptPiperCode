from enum import StrEnum

from pydantic import BaseModel, Field


class VagueLanguageCategory(StrEnum):
    LAZY_ADJECTIVE = "lazy_adjective"
    CATCH_ALL_NOUN = "catch_all_noun"


class VagueLanguageFinding(BaseModel):
    """One vague token occurrence in the optimized prompt body."""

    id: str
    term: str
    category: VagueLanguageCategory
    line_number: int = Field(ge=1)
    line: str
    start: int = Field(ge=0, description="Start offset of the term within `line`.")
    end: int = Field(ge=0, description="End offset of the term within `line`.")
    resolved: bool = False


class SemanticPrecisionResult(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    findings: list[VagueLanguageFinding] = Field(default_factory=list)
    vague_token_count: int = Field(ge=0)
    total_token_count: int = Field(ge=0)
