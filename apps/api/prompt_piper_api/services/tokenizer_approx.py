from __future__ import annotations

import re

_WORD_RE = re.compile(r"\b[\w'-]+\b", re.UNICODE)


def estimate_token_cost(text: str) -> int:
    """Local tokenizer approximation without external model calls."""
    if not text.strip():
        return 0
    words = _WORD_RE.findall(text)
    char_count = len(text)
    word_estimate = int(len(words) * 1.35)
    char_estimate = int(char_count / 4)
    punctuation_bonus = text.count("\n") // 3
    return max(1, (word_estimate + char_estimate) // 2 + punctuation_bonus)
