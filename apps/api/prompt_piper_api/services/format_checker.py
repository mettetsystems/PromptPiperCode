from __future__ import annotations

import re

_PLAIN_TEXT_FORBIDDEN = (
    re.compile(r"^#{1,6}\s", re.MULTILINE),
    re.compile(r"<[^>]+>"),
    re.compile(r"\*\*[^*]+\*\*"),
    re.compile(r"```"),
)

_EXPECTED_SECTIONS = (
    "mission",
    "context",
    "constraints",
    "style",
    "output contract",
    "acceptance",
)


def format_adherence_score(body: str) -> float:
    """Return 1.00 when the prompt follows the plain-text section contract."""
    if not body.strip():
        return 0.0
    for pattern in _PLAIN_TEXT_FORBIDDEN:
        if pattern.search(body):
            return 0.0
    lowered = body.lower()
    section_hits = sum(1 for section in _EXPECTED_SECTIONS if section in lowered)
    if section_hits < 3:
        return 0.0
    if not re.search(r"^[A-Za-z].+\n[-]{3,}", body, re.MULTILINE):
        return 0.0
    return 1.0
