from __future__ import annotations

from pathlib import Path

from prompt_piper_api.domain.artifacts import ArtifactManifest
from prompt_piper_api.domain.requirement_card import RequirementCard
from prompt_piper_api.schemas.registry import RegistryPromptDetail
from prompt_piper_api.services.artifact_service import ArtifactService
from prompt_piper_api.services.git_registry_service import GitRegistryService
from prompt_piper_api.services.path_safety import (
    safe_child_path,
    validate_filename,
    validate_prompt_id,
)


class RegistryBrowseService:
    """Read finalized prompts and generated artifacts from local disk."""

    def __init__(self, registry_path: Path, artifacts_path: Path) -> None:
        self._registry = GitRegistryService(registry_path)
        self._artifacts_path = artifacts_path

    @property
    def registry(self) -> GitRegistryService:
        return self._registry

    def get_prompt_detail(self, prompt_id: str) -> RegistryPromptDetail | None:
        try:
            prompt_id = validate_prompt_id(prompt_id)
        except Exception:
            return None

        metadata = self._registry.load_metadata(prompt_id)
        if metadata is None:
            return None

        card_raw = self._registry.read_registry_file(prompt_id, "requirement_card.json")
        requirement_card = (
            RequirementCard.model_validate_json(card_raw)
            if card_raw
            else RequirementCard()
        )
        canonical = self._registry.read_registry_file(prompt_id, "canonical_prompt.txt") or ""

        artifact_dir = ArtifactService.resolve_latest_artifact_dir(self._artifacts_path, prompt_id)
        manifest: ArtifactManifest | None = None
        if artifact_dir is not None:
            manifest_path = artifact_dir / "artifact_manifest.json"
            if manifest_path.is_file():
                manifest = ArtifactManifest.model_validate_json(
                    manifest_path.read_text(encoding="utf-8")
                )

        return RegistryPromptDetail(
            metadata=metadata,
            requirement_card=requirement_card,
            canonical_prompt=canonical,
            artifact_manifest=manifest,
            artifact_dir=str(artifact_dir) if artifact_dir is not None else None,
        )

    def _artifact_dir_for(self, prompt_id: str) -> Path | None:
        try:
            prompt_id = validate_prompt_id(prompt_id)
        except Exception:
            return None
        return ArtifactService.resolve_latest_artifact_dir(self._artifacts_path, prompt_id)

    def read_artifact_file(self, prompt_id: str, filename: str) -> tuple[str, str] | None:
        """Return (content, media_type) for a file under the latest artifact export."""
        try:
            prompt_id = validate_prompt_id(prompt_id)
            filename = validate_filename(filename)
        except Exception:
            return None

        artifact_dir = self._artifact_dir_for(prompt_id)
        if artifact_dir is None:
            return None

        target = safe_child_path(artifact_dir, filename)
        if target is None or not target.is_file():
            return None

        if filename.endswith(".json"):
            media_type = "application/json"
        elif filename.endswith(".yaml") or filename.endswith(".yml"):
            media_type = "text/yaml"
        elif filename.endswith(".md"):
            media_type = "text/markdown"
        elif filename.endswith(".html"):
            media_type = "text/html"
        elif filename.endswith(".pdf"):
            return None
        else:
            media_type = "text/plain"

        return target.read_text(encoding="utf-8"), media_type

    def read_artifact_bytes(self, prompt_id: str, filename: str) -> tuple[bytes, str] | None:
        try:
            prompt_id = validate_prompt_id(prompt_id)
            filename = validate_filename(filename)
        except Exception:
            return None

        artifact_dir = self._artifact_dir_for(prompt_id)
        if artifact_dir is None:
            return None

        target = safe_child_path(artifact_dir, filename)
        if target is None or not target.is_file():
            return None

        if filename.endswith(".pdf"):
            media_type = "application/pdf"
        elif filename.endswith(".json"):
            media_type = "application/json"
        else:
            media_type = "application/octet-stream"
        return target.read_bytes(), media_type
