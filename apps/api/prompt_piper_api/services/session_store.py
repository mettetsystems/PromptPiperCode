from __future__ import annotations

from pathlib import Path
from typing import Protocol
from uuid import UUID

from prompt_piper_api.services.session_record import SessionRecord


class SessionStore(Protocol):
    def get(self, session_id: UUID) -> SessionRecord | None: ...

    def save(self, record: SessionRecord) -> None: ...


class InMemorySessionStore:
    """Ephemeral session storage for unit tests."""

    def __init__(self) -> None:
        self._records: dict[UUID, SessionRecord] = {}

    def get(self, session_id: UUID) -> SessionRecord | None:
        return self._records.get(session_id)

    def save(self, record: SessionRecord) -> None:
        self._records[record.session.id] = record


class FileSessionStore:
    """Persist each workflow session as JSON under a directory."""

    def __init__(self, root: Path) -> None:
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, session_id: UUID) -> Path:
        return self._root / f"{session_id}.json"

    def get(self, session_id: UUID) -> SessionRecord | None:
        path = self._path(session_id)
        if not path.is_file():
            return None
        return SessionRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def save(self, record: SessionRecord) -> None:
        path = self._path(record.session.id)
        path.write_text(
            record.model_dump_json(indent=2),
            encoding="utf-8",
        )


def create_session_store(sessions_path: Path) -> SessionStore:
    return FileSessionStore(sessions_path)
