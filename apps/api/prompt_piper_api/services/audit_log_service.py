from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from prompt_piper_api.domain.audit import AuditEvent
from prompt_piper_api.domain.inference import ExternalInferenceAuditEvent
from prompt_piper_api.domain.limits import MAX_AUDIT_MESSAGE_CHARS
from prompt_piper_api.services.logging_config import redact_secrets

T = TypeVar("T", bound=BaseModel)


class AuditLogService:
    """Append-only local audit log for privacy-sensitive and registry actions."""

    def __init__(self, audit_log_path: Path) -> None:
        self._audit_log_path = audit_log_path
        self._events_file = audit_log_path / "events.jsonl"
        self._inference_file = audit_log_path / "external_inference.jsonl"

    @property
    def events_file(self) -> Path:
        return self._events_file

    @property
    def inference_log_file(self) -> Path:
        return self._inference_file

    def log_event(self, event: AuditEvent) -> None:
        self._audit_log_path.mkdir(parents=True, exist_ok=True)
        payload = event.model_dump(mode="json")
        payload["timestamp"] = event.timestamp.isoformat()
        if payload.get("message"):
            payload["message"] = redact_secrets(str(payload["message"]))[:MAX_AUDIT_MESSAGE_CHARS]
        with self._events_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")

    def log_external_inference_attempt(self, event: ExternalInferenceAuditEvent) -> None:
        self._audit_log_path.mkdir(parents=True, exist_ok=True)
        payload = event.model_dump(mode="json")
        payload["timestamp"] = event.timestamp.isoformat()
        if payload.get("error_message"):
            payload["error_message"] = redact_secrets(str(payload["error_message"]))[
                :MAX_AUDIT_MESSAGE_CHARS
            ]
        with self._inference_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")

    def read_events(self) -> list[AuditEvent]:
        return self._read_lines(self._events_file, AuditEvent)

    def read_external_inference_events(self) -> list[ExternalInferenceAuditEvent]:
        return self._read_lines(self._inference_file, ExternalInferenceAuditEvent)

    @staticmethod
    def _read_lines(path: Path, model: type[T]) -> list[T]:
        if not path.is_file():
            return []
        items: list[T] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            items.append(model.model_validate_json(line))
        return items
