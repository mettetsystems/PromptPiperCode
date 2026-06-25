from pathlib import Path

from prompt_piper_api.services.artifact_export_service import ArtifactExportService
from prompt_piper_api.services.artifact_service import ArtifactService


def build_test_export_service(base_path: Path) -> ArtifactExportService:
    """Wire export paths for tests using a temporary directory."""
    artifact_root = base_path / "exports"
    artifact_root.mkdir(parents=True, exist_ok=True)
    return ArtifactExportService(
        ArtifactService(artifact_root),
        export_root=base_path,
        host_export_root=base_path,
        artifact_root=artifact_root,
    )
