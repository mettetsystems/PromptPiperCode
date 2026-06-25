from datetime import datetime

from prompt_piper_api.domain.artifacts import ArtifactManifest
from prompt_piper_api.domain.registry import RegistryMetadata
from prompt_piper_api.domain.requirement_card import RequirementCard
from pydantic import BaseModel, Field


class RegistryPromptSummary(BaseModel):
    prompt_id: str
    version: int = Field(ge=1)
    title: str
    abstract: str = ""
    tags: list[str] = Field(default_factory=list)
    output_form: str = ""
    evaluation_scores: dict[str, float] = Field(default_factory=dict)
    artifact_paths: dict[str, str] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class RegistryPromptDetail(BaseModel):
    metadata: RegistryMetadata
    requirement_card: RequirementCard
    canonical_prompt: str = ""
    artifact_manifest: ArtifactManifest | None = None
    artifact_dir: str | None = None


def to_registry_summary(metadata: RegistryMetadata) -> RegistryPromptSummary:
    return RegistryPromptSummary(
        prompt_id=metadata.prompt_id,
        version=metadata.version,
        title=metadata.title,
        abstract=metadata.abstract,
        tags=list(metadata.tags),
        output_form=metadata.output_form,
        evaluation_scores=dict(metadata.evaluation_scores),
        artifact_paths=dict(metadata.artifact_paths),
        created_at=metadata.created_at,
        updated_at=metadata.updated_at,
    )
