from __future__ import annotations

import re

from prompt_piper_api.domain.optimization import ConstraintGraph, ConstraintSlot
from prompt_piper_api.domain.requirement_card import RequirementCard, OptimizationTargets
from prompt_piper_api.services.embedding_service import EmbeddingService
from prompt_piper_api.services.similarity_utils import cosine_similarity, lexical_overlap_score, tokenize

_SECTION_TITLE = re.compile(
    r"^(Mission|Context|Constraints|Style|Output contract|Acceptance criteria|"
    r"Acceptance tests|Forbidden content or actions|Tools|Artifact rules)$",
    re.IGNORECASE,
)
_DIVIDER = re.compile(r"^-+$")
_VAGUE_FOR_CAPTURE = re.compile(
    r"\b(maybe|perhaps|somewhat|kind of|sort of|very|really|just)\b",
    re.I,
)

# Embedding similarity required to treat a paraphrase as captured.
EMBEDDING_CAPTURE_THRESHOLD = 0.78
# Token overlap fallback when embeddings are unavailable or inconclusive.
LEXICAL_CAPTURE_THRESHOLD = 0.55
# Shorter, more precise wording (e.g. "propeller" for "fan-like part of a plane").
PRECISE_REFINEMENT_THRESHOLD = 0.82
PRECISE_REFINEMENT_MAX_TOKEN_RATIO = 0.72

_BINDING_CAPTURE_SLOTS: tuple[ConstraintSlot, ...] = (
    ConstraintSlot.OBJECTIVE,
    ConstraintSlot.AUDIENCE,
    ConstraintSlot.SCOPE,
    ConstraintSlot.FORMAT,
    ConstraintSlot.MUST_CITE,
    ConstraintSlot.EXCLUSIONS,
    ConstraintSlot.TOKEN_BUDGET,
)

_LANGUAGE_ALIASES: dict[str, tuple[str, ...]] = {
    "en": ("en", "english"),
    "es": ("es", "spanish", "español"),
    "fr": ("fr", "french", "français"),
    "de": ("de", "german", "deutsch"),
}


def normalize_phrase_for_capture(phrase: str) -> str:
    """Normalize text for capture checks so denoising tweaks do not fail the gate."""
    collapsed = _VAGUE_FOR_CAPTURE.sub("", phrase)
    normalized = re.sub(r"\s+", " ", collapsed).strip().lower()
    return normalized.rstrip(".,;:")


def dedupe_phrases(phrases: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for phrase in phrases:
        key = normalize_phrase_for_capture(phrase)
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(phrase.strip())
    return unique


def collect_requirement_phrases(card: RequirementCard) -> list[str]:
    """Return each populated requirement phrase that must be reflected in the prompt body."""
    phrases: list[str] = []

    string_fields = (
        "objective",
        "context_background",
        "audience",
        "persona_role",
        "desired_output_shape",
        "tone_style",
        "verbosity",
        "language",
    )
    for field_name in string_fields:
        value = getattr(card, field_name, "")
        if isinstance(value, str) and value.strip():
            phrases.append(value.strip())

    list_fields = (
        "constraints",
        "success_criteria",
        "forbidden_content_actions",
        "input_materials",
        "example_outputs",
        "edge_cases",
    )
    for field_name in list_fields:
        values: list[str] = getattr(card, field_name)
        phrases.extend(item.strip() for item in values if item.strip())

    targets: OptimizationTargets = card.optimization_targets
    for label, value in targets.model_dump().items():
        if value and str(value).strip():
            phrases.append(str(value).strip())

    return phrases


def collect_optimization_binding_phrases(
    graph: ConstraintGraph,
    card: RequirementCard,
) -> list[str]:
    """Phrases the optimizer must preserve and the approval gate scores for optimized prompts."""
    phrases: list[str] = []
    for slot in _BINDING_CAPTURE_SLOTS:
        phrases.extend(graph.slots.get(slot.value, []))
    for value in (card.context_background, card.tone_style, card.language):
        if value.strip():
            phrases.append(value.strip())
    return dedupe_phrases(phrases)


def body_chunks(body: str) -> list[str]:
    """Split the prompt into lines and short multi-line windows for semantic matching."""
    lines: list[str] = []
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line or _DIVIDER.match(line) or _SECTION_TITLE.match(line):
            continue
        lines.append(line)

    chunks = list(lines)
    for index in range(len(lines) - 1):
        pair = f"{lines[index]} {lines[index + 1]}".strip()
        if len(pair.split()) >= 4:
            chunks.append(pair)

    stripped = body.strip()
    if stripped and stripped not in chunks:
        chunks.append(stripped)
    return chunks


class RequirementCaptureEvaluator:
    """Score whether an optimized prompt captures requirement concepts, not just verbatim text."""

    def __init__(self, embedding: EmbeddingService | None = None) -> None:
        self._embedding = embedding or EmbeddingService(prefer_fallback=True)

    def score(
        self,
        body: str,
        card: RequirementCard,
        *,
        constraint_graph: ConstraintGraph | None = None,
    ) -> float:
        if constraint_graph is not None:
            phrases = collect_optimization_binding_phrases(constraint_graph, card)
        else:
            phrases = collect_requirement_phrases(card)
        if not phrases:
            return 1.0

        chunks = body_chunks(body)
        captured = sum(1 for phrase in phrases if self.captures_phrase(phrase, body, chunks))
        return round(captured / len(phrases), 2)

    def captures_phrase(self, requirement: str, body: str, chunks: list[str]) -> bool:
        phrase = requirement.strip()
        if not phrase:
            return True

        lowered_body = body.lower()
        if phrase.lower() in lowered_body:
            return True

        normalized_phrase = normalize_phrase_for_capture(phrase)
        normalized_body = normalize_phrase_for_capture(body)
        if normalized_phrase and normalized_phrase in normalized_body:
            return True

        if self._language_alias_captured(phrase, lowered_body):
            return True

        if chunks:
            normalized_chunks = [normalize_phrase_for_capture(chunk) for chunk in chunks]
            best_lexical = max(
                lexical_overlap_score(phrase, chunk) for chunk in chunks
            )
            if best_lexical >= LEXICAL_CAPTURE_THRESHOLD:
                return True
            best_normalized = max(
                (
                    lexical_overlap_score(normalized_phrase, chunk)
                    for chunk in normalized_chunks
                    if normalized_phrase
                ),
                default=0.0,
            )
            if best_normalized >= LEXICAL_CAPTURE_THRESHOLD:
                return True

        if not chunks:
            return False

        phrase_embedding = self._embedding.embed_one(phrase)
        chunk_embeddings = self._embedding.embed(chunks)
        phrase_tokens = max(len(tokenize(phrase)), 1)

        for chunk, chunk_embedding in zip(chunks, chunk_embeddings, strict=True):
            similarity = cosine_similarity(phrase_embedding, chunk_embedding)
            chunk_tokens = max(len(tokenize(chunk)), 1)

            if similarity >= EMBEDDING_CAPTURE_THRESHOLD:
                return True

            if (
                similarity >= PRECISE_REFINEMENT_THRESHOLD
                and chunk_tokens <= phrase_tokens * PRECISE_REFINEMENT_MAX_TOKEN_RATIO
            ):
                # More precise wording that preserves the same concept (fewer tokens).
                return True

        return False

    @staticmethod
    def _language_alias_captured(phrase: str, lowered_body: str) -> bool:
        normalized = phrase.strip().lower()
        aliases = _LANGUAGE_ALIASES.get(normalized)
        if aliases is None:
            return False
        return any(alias in lowered_body for alias in aliases)
