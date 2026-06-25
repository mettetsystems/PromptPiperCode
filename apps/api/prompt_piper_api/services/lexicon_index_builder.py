from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from prompt_piper_api.domain.lexicon_index import LexiconEntrySource, LexiconVectorRecord
from prompt_piper_api.domain.precision import VagueLanguageCategory
from prompt_piper_api.services.semantic_precision import CATCH_ALL_NOUNS, LAZY_ADJECTIVES
from prompt_piper_api.services.wordnet_lexicon import WordNetLexicon, _is_usable_candidate, _lemma_label

_POS_FILTER = {
    VagueLanguageCategory.LAZY_ADJECTIVE: frozenset({"a", "s"}),
    VagueLanguageCategory.CATCH_ALL_NOUN: frozenset({"n"}),
}
_VAGUE_TERMS = LAZY_ADJECTIVES | CATCH_ALL_NOUNS
_BATCH_SIZE = 64


@dataclass(frozen=True)
class LexiconIndexBuildResult:
    entry_count: int
    output_path: str
    embedding_model: str


def build_lexicon_index_records(lexicon: WordNetLexicon | None = None) -> list[LexiconVectorRecord]:
    """Collect WordNet synset + glossary rows to embed (no vectors yet)."""
    source_lexicon = lexicon or WordNetLexicon()
    records: list[LexiconVectorRecord] = []
    seen_candidates: set[str] = set()

    records.extend(_glossary_records(source_lexicon, seen_candidates))
    records.extend(_wordnet_records(source_lexicon, seen_candidates))
    return records


def _glossary_records(
    lexicon: WordNetLexicon,
    seen_candidates: set[str],
) -> list[LexiconVectorRecord]:
    records: list[LexiconVectorRecord] = []
    seen_entries: set[int] = set()
    for entry in lexicon._glossary.values():  # noqa: SLF001
        if id(entry) in seen_entries:
            continue
        seen_entries.add(id(entry))
        for suggestion in entry.suggestions:
            lowered = suggestion.lower()
            if lowered in seen_candidates:
                continue
            seen_candidates.add(lowered)
            replaces = ", ".join(sorted(entry.replaces))
            text = (
                f"Prompt precision replacement: {suggestion}. "
                f"Use instead of vague words such as {replaces}."
            )
            records.append(
                LexiconVectorRecord(
                    id=_record_id("glossary", suggestion),
                    candidate=suggestion,
                    pos="n",
                    source=LexiconEntrySource.GLOSSARY,
                    text=text,
                )
            )
    return records


def _wordnet_records(
    lexicon: WordNetLexicon,
    seen_candidates: set[str],
) -> list[LexiconVectorRecord]:
    wordnet = lexicon._ensure_wordnet()  # noqa: SLF001
    if wordnet is None:
        return []

    records: list[LexiconVectorRecord] = []
    for synset in wordnet.all_synsets():
        pos = synset.pos()
        if pos not in {"n", "a", "s"}:
            continue
        lemmas = [_lemma_label(lemma.name()) for lemma in synset.lemmas()]
        usable = [
            lemma
            for lemma in lemmas
            if lemma.lower() not in _VAGUE_TERMS and re.fullmatch(r"[a-z0-9][a-z0-9 \-']*", lemma.lower())
        ]
        if not usable:
            continue
        candidate = usable[0]
        lowered = candidate.lower()
        if lowered in seen_candidates:
            continue
        seen_candidates.add(lowered)
        alt = ", ".join(usable[1:6])
        text = f"{pos}: {synset.definition().strip()}"
        if alt:
            text = f"{text} | related terms: {alt}"
        records.append(
            LexiconVectorRecord(
                id=_record_id("wordnet", synset.name()),
                candidate=candidate,
                pos=pos,
                source=LexiconEntrySource.WORDNET,
                text=text,
            )
        )
    return records


def _record_id(prefix: str, value: str) -> str:
    digest = hashlib.sha256(f"{prefix}:{value}".encode()).hexdigest()[:16]
    return f"{prefix}-{digest}"


def embed_lexicon_records(
    records: list[LexiconVectorRecord],
    *,
    embedding_model: str,
    batch_size: int = _BATCH_SIZE,
) -> list[LexiconVectorRecord]:
    from prompt_piper_api.services.embedding_service import EmbeddingService

    embedding = EmbeddingService(model_name=embedding_model, prefer_fallback=False, device="cpu")
    if embedding.using_fallback:
        msg = (
            "Sentence Transformers is required to build the lexicon vector index. "
            "Install sentence-transformers in the API venv."
        )
        raise RuntimeError(msg)

    embedded: list[LexiconVectorRecord] = []
    for start in range(0, len(records), batch_size):
        batch = records[start : start + batch_size]
        vectors = embedding.embed([record.text for record in batch])
        for record, vector in zip(batch, vectors, strict=True):
            embedded.append(record.model_copy(update={"embedding": vector}))
    return embedded


def build_lexicon_vector_index(
    output_path: Any,
    *,
    lexicon: WordNetLexicon | None = None,
    embedding_model: str | None = None,
) -> LexiconIndexBuildResult:
    from pathlib import Path

    from prompt_piper_api.config import get_settings
    from prompt_piper_api.domain.lexicon_index import LexiconVectorIndexManifest
    from prompt_piper_api.services.lexicon_vector_index import LexiconVectorIndex

    settings = get_settings()
    resolved_model = embedding_model or settings.prompt_piper_embedding_model
    records = build_lexicon_index_records(lexicon)
    embedded = embed_lexicon_records(records, embedding_model=resolved_model)
    manifest = LexiconVectorIndexManifest(
        embedding_model=resolved_model,
        entry_count=len(embedded),
        built_at=datetime.now(tz=UTC).isoformat(),
        entries=embedded,
    )
    path = Path(output_path)
    LexiconVectorIndex.write_manifest(path, manifest)
    return LexiconIndexBuildResult(
        entry_count=len(embedded),
        output_path=str(path),
        embedding_model=resolved_model,
    )
