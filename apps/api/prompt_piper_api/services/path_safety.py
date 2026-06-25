from __future__ import annotations

import re
from pathlib import Path

from prompt_piper_api.domain.errors import ErrorCode
from prompt_piper_api.services.exceptions import InvalidPathError, InvalidPromptIdError

_PROMPT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*-[0-9a-f]{8}$")
_SAFE_FILENAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def validate_prompt_id(prompt_id: str) -> str:
    """Reject path traversal and malformed prompt IDs."""
    cleaned = prompt_id.strip()
    if not cleaned or not _PROMPT_ID_RE.fullmatch(cleaned):
        raise InvalidPromptIdError(
            "Prompt ID must match slug-{8-char-hex} format.",
            prompt_id=cleaned,
        )
    return cleaned


def validate_filename(filename: str) -> str:
    """Reject directory traversal in artifact/registry filenames."""
    cleaned = filename.strip()
    if (
        not cleaned
        or cleaned.startswith(".")
        or "/" in cleaned
        or "\\" in cleaned
        or ".." in cleaned
    ):
        raise InvalidPathError("Invalid filename.", filename=cleaned)
    if not _SAFE_FILENAME_RE.fullmatch(cleaned):
        raise InvalidPathError("Filename contains disallowed characters.", filename=cleaned)
    return cleaned


def safe_child_path(base: Path, *parts: str) -> Path | None:
    """Resolve a path under base; return None if it escapes base."""
    try:
        base_resolved = base.resolve()
        target = base_resolved.joinpath(*parts).resolve()
    except (OSError, ValueError):
        return None
    if base_resolved == target:
        return target
    if base_resolved not in target.parents:
        return None
    return target


def artifact_version_dir(artifacts_root: Path, prompt_id: str, version: int) -> Path:
    """Return the versioned artifact directory for a prompt export."""
    validate_prompt_id(prompt_id)
    if version < 1:
        msg = "Artifact version must be >= 1."
        raise ValueError(msg)
    return artifacts_root / prompt_id / f"v{version:03d}"


def artifact_version_label(version: int) -> str:
    return f"v{version:03d}"


def error_code_for_path_exception(exc: InvalidPathError | InvalidPromptIdError) -> ErrorCode:
    if isinstance(exc, InvalidPromptIdError):
        return ErrorCode.INVALID_PROMPT_ID
    return ErrorCode.INVALID_PATH
