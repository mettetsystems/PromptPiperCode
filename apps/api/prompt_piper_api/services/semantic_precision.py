from __future__ import annotations

import hashlib
import re

from prompt_piper_api.domain.precision import (
    SemanticPrecisionResult,
    VagueLanguageCategory,
    VagueLanguageFinding,
)

# Lazy adjectives and catch-all nouns that weaken prompt precision (case-insensitive, word boundaries).
LAZY_ADJECTIVES: frozenset[str] = frozenset(
    {
        "good",
        "bad",
        "nice",
        "fine",
        "great",
        "awesome",
        "interesting",
        "cool",
        "okay",
        "ok",
        "decent",
        "appropriate",
        "relevant",
        "significant",
        "special",
        "different",
        "various",
        "several",
        "many",
        "few",
        "huge",
        "small",
        "big",
        "random",
        "weird",
        "normal",
    }
)

CATCH_ALL_NOUNS: frozenset[str] = frozenset(
    {
        "thing",
        "stuff",
        "something",
        "anything",
        "everything",
        "item",
        "object",
        "matter",
        "affair",
        "business",
        "deal",
        "phenomenon",
        "concept",
        "aspect",
        "element",
        "factor",
        "area",
        "field",
        "situation",
        "circumstance",
        "event",
        "issue",
        "problem",
        "detail",
        "component",
        "bit",
    }
)

PRECISION_THRESHOLD = 0.75
# Each vague hit reduces score; tuned so ~4 hits in a medium prompt ≈ below threshold.
VAGUE_HIT_PENALTY = 0.08


def _category_for_term(term: str) -> VagueLanguageCategory:
    lowered = term.lower()
    if lowered in LAZY_ADJECTIVES:
        return VagueLanguageCategory.LAZY_ADJECTIVE
    return VagueLanguageCategory.CATCH_ALL_NOUN


def _finding_id(line_number: int, term: str, start: int) -> str:
    raw = f"{line_number}:{term.lower()}:{start}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


class SemanticPrecisionEvaluator:
    """Score prompt text for vague language using deterministic regex matching."""

    def evaluate(self, body: str) -> SemanticPrecisionResult:
        if not body.strip():
            return SemanticPrecisionResult(
                score=1.0,
                findings=[],
                vague_token_count=0,
                total_token_count=0,
            )

        findings: list[VagueLanguageFinding] = []
        vague_terms: set[str] = set()
        total_tokens = len(body.split())

        pattern = re.compile(
            r"\b(" + "|".join(re.escape(word) for word in sorted(LAZY_ADJECTIVES | CATCH_ALL_NOUNS, key=len, reverse=True)) + r")\b",
            re.IGNORECASE,
        )

        for line_number, raw_line in enumerate(body.splitlines(), start=1):
            display_line = raw_line.rstrip()
            stripped = raw_line.strip()
            if not stripped:
                continue
            leading = len(raw_line) - len(raw_line.lstrip())
            for match in pattern.finditer(stripped):
                term = match.group(1)
                vague_terms.add(term.lower())
                start = leading + match.start()
                end = leading + match.end()
                findings.append(
                    VagueLanguageFinding(
                        id=_finding_id(line_number, term, match.start()),
                        term=term,
                        category=_category_for_term(term),
                        line_number=line_number,
                        line=display_line,
                        start=start,
                        end=end,
                        resolved=False,
                    )
                )

        vague_count = len(vague_terms)
        penalty = min(1.0, len(findings) * VAGUE_HIT_PENALTY)
        score = round(max(0.0, 1.0 - penalty), 2)

        return SemanticPrecisionResult(
            score=score,
            findings=findings,
            vague_token_count=vague_count,
            total_token_count=total_tokens,
        )

    @staticmethod
    def apply_replacement(
        body: str,
        *,
        line_number: int,
        term: str,
        replacement: str,
        start: int | None = None,
        end: int | None = None,
    ) -> str:
        """Replace one occurrence of term on the given line with literal text.

        The replacement may be a word or a phrase. It is inserted as-is so
        backslashes, digits, and punctuation are not treated as regex syntax.
        """
        cleaned = replacement.strip()
        if not cleaned:
            msg = "Replacement text cannot be empty."
            raise ValueError(msg)

        lines = body.splitlines()
        if line_number < 1 or line_number > len(lines):
            msg = f"Line number {line_number} is out of range."
            raise ValueError(msg)

        index = line_number - 1
        line = lines[index]
        if start is not None and end is not None:
            if 0 <= start < end <= len(line) and line[start:end].lower() == term.lower():
                lines[index] = line[:start] + cleaned + line[end:]
                return "\n".join(lines)

        updated = _replace_first_whole_token(line, term, cleaned)
        if updated is None:
            msg = f"Could not find '{term}' on line {line_number}."
            raise ValueError(msg)

        lines[index] = updated
        return "\n".join(lines)


def _is_token_char(char: str) -> bool:
    return char.isalnum() or char == "_"


def _replace_first_whole_token(line: str, term: str, replacement: str) -> str | None:
    """Replace the first whole-token occurrence of term without using re.sub."""
    lowered = line.lower()
    needle = term.lower()
    search_from = 0
    while True:
        pos = lowered.find(needle, search_from)
        if pos < 0:
            return None
        end = pos + len(needle)
        before_ok = pos == 0 or not _is_token_char(line[pos - 1])
        after_ok = end >= len(line) or not _is_token_char(line[end])
        if before_ok and after_ok:
            return line[:pos] + replacement + line[end:]
        search_from = pos + 1
