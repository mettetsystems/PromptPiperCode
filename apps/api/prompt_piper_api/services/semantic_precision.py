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
            line = raw_line.strip()
            if not line:
                continue
            for match in pattern.finditer(line):
                term = match.group(1)
                vague_terms.add(term.lower())
                findings.append(
                    VagueLanguageFinding(
                        id=_finding_id(line_number, term, match.start()),
                        term=term,
                        category=_category_for_term(term),
                        line_number=line_number,
                        line=raw_line.rstrip(),
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
    def apply_replacement(body: str, *, line_number: int, term: str, replacement: str) -> str:
        """Replace the first word-boundary occurrence of term on the given line."""
        if not replacement.strip():
            msg = "Replacement text cannot be empty."
            raise ValueError(msg)

        lines = body.splitlines()
        if line_number < 1 or line_number > len(lines):
            msg = f"Line number {line_number} is out of range."
            raise ValueError(msg)

        index = line_number - 1
        pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
        updated, count = pattern.subn(replacement.strip(), lines[index], count=1)
        if count == 0:
            msg = f"Could not find '{term}' on line {line_number}."
            raise ValueError(msg)

        lines[index] = updated
        return "\n".join(lines)
