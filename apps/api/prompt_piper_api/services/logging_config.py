from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from typing import Any

_REDACT_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?i)(api[_-]?key\s*[:=]\s*)[^\s,;'\"]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(authorization\s*[:=]\s*)[^\s,;'\"]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._\-]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(sk-[A-Za-z0-9]{8,})"), "[REDACTED]"),
    (re.compile(r"(?i)(password\s*[:=]\s*)[^\s,;'\"]+"), r"\1[REDACTED]"),
)


def redact_secrets(text: str) -> str:
    """Remove likely secrets from log and audit strings."""
    redacted = text
    for pattern, replacement in _REDACT_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted[:2048]


class StructuredFormatter(logging.Formatter):
    """Emit JSON log lines for machine parsing."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": redact_secrets(record.getMessage()),
        }
        if record.exc_info and record.exc_info[1] is not None:
            payload["exception"] = redact_secrets(str(record.exc_info[1]))
        for key in ("code", "action", "session_id", "prompt_id", "state"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload, sort_keys=True)


def configure_logging(*, level: int = logging.INFO) -> None:
    """Configure root logger with structured JSON output."""
    root = logging.getLogger()
    if root.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter())
    root.addHandler(handler)
    root.setLevel(level)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
