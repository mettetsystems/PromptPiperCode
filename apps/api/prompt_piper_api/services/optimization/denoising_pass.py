from __future__ import annotations

import re

from prompt_piper_api.services.requirement_capture import normalize_phrase_for_capture

_VAGUE = re.compile(r"\b(maybe|perhaps|somewhat|kind of|sort of|very|really|just)\b", re.I)
_FILLER = re.compile(
    r"\b(please note that|it is important to|in order to|at this point in time)\b",
    re.I,
)
_UNSUPPORTED = re.compile(r"\b(as mentioned above|as stated earlier|see above)\b", re.I)
_HEDGING = re.compile(r"\b(might|could potentially|it seems that)\b", re.I)


class DenoisingPass:
    """Pass 3: remove repetition, filler, hedging, and unsupported references."""

    def run(
        self,
        body: str,
        *,
        protected_phrases: list[str] | None = None,
    ) -> tuple[str, list[str]]:
        protected_keys = {
            normalize_phrase_for_capture(phrase)
            for phrase in (protected_phrases or [])
            if phrase.strip()
        }
        removed: list[str] = []
        lines = [line.strip() for line in body.splitlines()]
        deduped: list[str] = []
        seen: set[str] = set()

        for line in lines:
            normalized = re.sub(r"\s+", " ", line.lower())
            if normalized and normalized in seen:
                removed.append(f"Repeated line: {line}")
                continue
            if normalized:
                seen.add(normalized)
            deduped.append(line)

        cleaned_lines: list[str] = []
        for line in deduped:
            original = line
            if self._line_is_protected(line, protected_keys):
                cleaned_lines.append(line)
                continue
            line = _FILLER.sub("", line)
            line = _UNSUPPORTED.sub("", line)
            line = _HEDGING.sub("", line)
            line = _VAGUE.sub("", line)
            line = re.sub(r"\s{2,}", " ", line).strip()
            if original != line and original.strip():
                removed.append(f"Filler or vague phrasing: {original}")
            if line or not original.strip():
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines), removed

    @staticmethod
    def _line_is_protected(line: str, protected_keys: set[str]) -> bool:
        if not protected_keys:
            return False
        normalized_line = normalize_phrase_for_capture(line)
        if not normalized_line:
            return False
        return any(
            key in normalized_line or normalized_line in key for key in protected_keys if key
        )
