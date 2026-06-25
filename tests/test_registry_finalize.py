from pathlib import Path
from uuid import UUID

import pytest
import yaml
from prompt_piper_api.domain.enums import SessionState
from prompt_piper_api.services.exceptions import StateTransitionError
from prompt_piper_api.services.git_registry_service import GitRegistryService
from prompt_piper_api.services.session_service import SessionService
from tests.clarification_helpers import drive_session_to_edit


@pytest.fixture
def registry_path(tmp_path: Path) -> Path:
    return tmp_path / "registry"


@pytest.fixture
def registry(registry_path: Path) -> GitRegistryService:
    return GitRegistryService(registry_path)


@pytest.fixture
def service(registry: GitRegistryService) -> SessionService:
    return SessionService(llm=None, registry=registry)


def _enter_edit_state(service: SessionService) -> UUID:
    created = service.create_session(initial_request="Draft a weekly status update prompt")
    session_id = created.record.session.id
    drive_session_to_edit(
        service,
        session_id,
        answers=["Engineering managers", "Bulleted summary with risks"],
    )
    return session_id


def test_finalization_writes_registry_files(
    service: SessionService,
    registry_path: Path,
) -> None:
    session_id = _enter_edit_state(service)
    service.edit_draft(session_id, "Change tone to analytical")

    result = service.finalize(session_id)
    prompt_id = result.prompt_id
    assert prompt_id
    assert result.registry_warning is None

    prompt_dir = registry_path / prompt_id
    assert (prompt_dir / "metadata.yaml").is_file()
    assert (prompt_dir / "canonical_prompt.md").is_file()
    assert (prompt_dir / "canonical_prompt.txt").is_file()
    assert (prompt_dir / "requirement_card.json").is_file()
    assert (prompt_dir / "lineage.json").is_file()

    metadata = yaml.safe_load((prompt_dir / "metadata.yaml").read_text(encoding="utf-8"))
    assert metadata["prompt_id"] == prompt_id
    assert metadata["version"] == result.draft.version
    assert metadata["title"]
    assert "evaluation_scores" in metadata
    assert metadata["artifact_paths"]["canonical_txt"] == "canonical_prompt.txt"
    assert metadata["created_at"]
    assert metadata["updated_at"]

    assert "analytical" in (prompt_dir / "canonical_prompt.txt").read_text(encoding="utf-8")


def test_canonical_prompt_is_immutable_after_finalization(
    service: SessionService,
    registry_path: Path,
) -> None:
    session_id = _enter_edit_state(service)
    finalized = service.finalize(session_id)
    prompt_id = finalized.prompt_id
    assert prompt_id
    assert finalized.draft is not None
    assert finalized.draft.is_frozen is True
    assert finalized.draft.is_canonical is True

    prompt_dir = registry_path / prompt_id
    original_txt = (prompt_dir / "canonical_prompt.txt").read_text(encoding="utf-8")

    with pytest.raises(StateTransitionError):
        service.edit_draft(session_id, "Change tone to casual")

    assert (prompt_dir / "canonical_prompt.txt").read_text(encoding="utf-8") == original_txt


def test_metadata_is_human_readable_yaml(
    service: SessionService,
    registry_path: Path,
) -> None:
    session_id = _enter_edit_state(service)
    result = service.finalize(session_id)
    prompt_id = result.prompt_id
    assert prompt_id

    raw = (registry_path / prompt_id / "metadata.yaml").read_text(encoding="utf-8")
    assert "\n" in raw
    assert ": " in raw
    assert not raw.strip().startswith("{")

    metadata = yaml.safe_load(raw)
    for key in (
        "prompt_id",
        "version",
        "title",
        "abstract",
        "tags",
        "domain",
        "task_family",
        "output_form",
        "target_provider",
        "target_model",
        "preferred_prompt_length",
        "evaluation_scores",
        "artifact_paths",
        "created_at",
        "updated_at",
    ):
        assert key in metadata


def test_registry_can_initialize_without_existing_git_repo(
    registry_path: Path,
    service: SessionService,
) -> None:
    assert not registry_path.exists()

    session_id = _enter_edit_state(service)
    result = service.finalize(session_id)

    assert registry_path.is_dir()
    assert (registry_path / ".git").is_dir()
    assert result.registry_warning is None


def test_warning_returned_if_git_commit_fails(
    registry_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = GitRegistryService(registry_path)
    service = SessionService(llm=None, registry=registry)
    session_id = _enter_edit_state(service)

    def fail_commit(_prompt_id: str, _version: int) -> tuple[None, str]:
        return None, "Git commit failed: simulated failure"

    monkeypatch.setattr(registry, "_commit_prompt", fail_commit)

    result = service.finalize(session_id)
    prompt_id = result.prompt_id
    assert prompt_id
    assert result.registry_warning is not None
    assert "Git commit failed" in result.registry_warning

    prompt_dir = registry_path / prompt_id
    assert (prompt_dir / "metadata.yaml").is_file()
    assert (prompt_dir / "canonical_prompt.txt").is_file()


def test_finalize_assigns_prompt_id_and_preserves_session_state(
    service: SessionService,
) -> None:
    session_id = _enter_edit_state(service)
    result = service.finalize(session_id)

    record = service.get_session(session_id)
    assert record.session.prompt_id == result.prompt_id
    assert record.session.state is SessionState.SIMILARITY_CHECK
    assert result.draft is not None
    assert result.draft.is_canonical is True
