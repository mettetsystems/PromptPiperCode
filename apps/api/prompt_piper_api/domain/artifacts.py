from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field


class ArtifactFileEntry(BaseModel):
    """One generated file listed in the artifact manifest."""

    name: str
    format: str
    size_bytes: int = Field(ge=0)
    sha256: str = ""
    optional: bool = False


class ArtifactManifest(BaseModel):
    """Index of all files written for one Documents export folder."""

    export_id: str = Field(default_factory=lambda: str(uuid4()))
    prompt_id: str
    prompt_version: int = Field(ge=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    container_export_path: str
    expected_host_export_path: str
    files: list[ArtifactFileEntry] = Field(default_factory=list)
    generated_by: str = "prompt-piper"
    tool_versions: dict[str, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def version(self) -> int:
        return self.prompt_version

    @computed_field  # type: ignore[prop-decorator]
    @property
    def artifact_dir(self) -> str:
        return self.container_export_path

    @computed_field  # type: ignore[prop-decorator]
    @property
    def generated_at(self) -> datetime:
        return self.created_at

    @computed_field  # type: ignore[prop-decorator]
    @property
    def export_folder_host_path(self) -> str:
        return self.expected_host_export_path

    @computed_field  # type: ignore[prop-decorator]
    @property
    def export_folder_container_path(self) -> str:
        return self.container_export_path

    @computed_field  # type: ignore[prop-decorator]
    @property
    def generation_warnings(self) -> list[str]:
        return self.warnings

    @computed_field  # type: ignore[prop-decorator]
    @property
    def checksums(self) -> dict[str, str]:
        return {entry.name: entry.sha256 for entry in self.files if entry.sha256}


class ExportAuditRecord(BaseModel):
    """Audit metadata written alongside each export folder."""

    export_id: str
    prompt_id: str
    prompt_version: int = Field(ge=1)
    session_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    container_export_path: str
    expected_host_export_path: str
    file_count: int = Field(ge=0)
    warnings: list[str] = Field(default_factory=list)


class ArtifactGenerationResult(BaseModel):
    """Outcome of writing export artifacts for a finalized prompt."""

    export_id: str
    prompt_id: str
    version: int = Field(ge=1)
    container_export_path: str
    expected_host_export_path: str
    manifest_path: str
    generated_files: list[str] = Field(default_factory=list)
    manifest: ArtifactManifest
    artifact_paths: dict[str, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def artifact_dir(self) -> str:
        return self.container_export_path

    @computed_field  # type: ignore[prop-decorator]
    @property
    def export_folder_host_path(self) -> str:
        return self.expected_host_export_path

    @computed_field  # type: ignore[prop-decorator]
    @property
    def export_folder_container_path(self) -> str:
        return self.container_export_path
