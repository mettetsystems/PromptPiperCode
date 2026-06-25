from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return max(0.0, min(1.0, dot / (left_norm * right_norm)))


def serialize_embedding(values: list[float]) -> str:
    return json.dumps(values)


def deserialize_embedding(raw: str) -> list[float]:
    data: Any = json.loads(raw)
    if not isinstance(data, list):
        msg = "Embedding payload must be a JSON list"
        raise TypeError(msg)
    return [float(item) for item in data]


def hash_embed(text: str, *, dimensions: int = 384) -> list[float]:
    """Deterministic local fallback embedding for dev and tests."""
    vector = [
        (int.from_bytes(hashlib.sha256(f"{text}:{index}".encode()).digest()[:4], "big") / 2**32)
        * 2
        - 1
        for index in range(dimensions)
    ]
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0.0:
        return vector
    return [value / norm for value in vector]


def tokenize(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def lexical_overlap_score(query: str, document: str) -> float:
    query_tokens = tokenize(query)
    if not query_tokens:
        return 0.0
    document_tokens = tokenize(document)
    if not document_tokens:
        return 0.0
    overlap = len(query_tokens & document_tokens)
    return overlap / len(query_tokens)


def short_delta(new_text: str, prior_text: str) -> str:
    new_tokens = tokenize(new_text)
    old_tokens = tokenize(prior_text)
    added = sorted(new_tokens - old_tokens)[:8]
    removed = sorted(old_tokens - new_tokens)[:8]
    parts: list[str] = []
    if added:
        parts.append(f"Adds: {', '.join(added)}")
    if removed:
        parts.append(f"Removes: {', '.join(removed)}")
    return "; ".join(parts) if parts else "Prompts are nearly identical."
