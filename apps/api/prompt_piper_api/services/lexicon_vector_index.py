from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from prompt_piper_api.config import _repo_root, get_settings
from prompt_piper_api.domain.lexicon_index import LexiconVectorIndexManifest, LexiconVectorRecord
from prompt_piper_api.services.similarity_utils import cosine_similarity


class LexiconVectorIndex:
    """In-memory vector search over precision lexicon entries."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or self.default_path()
        self._manifest: LexiconVectorIndexManifest | None = None
        self._entries: list[LexiconVectorRecord] = []
        self._load()

    @staticmethod
    def default_path() -> Path:
        settings = get_settings()
        return settings.lexicon_vector_index_path

    @property
    def available(self) -> bool:
        return bool(self._entries)

    @property
    def embedding_model(self) -> str | None:
        return None if self._manifest is None else self._manifest.embedding_model

    @property
    def entry_count(self) -> int:
        return len(self._entries)

    def search(
        self,
        query_embedding: list[float],
        *,
        limit: int = 20,
        pos_filter: frozenset[str] | None = None,
    ) -> list[tuple[float, LexiconVectorRecord]]:
        if not self._entries or not query_embedding:
            return []

        scored: list[tuple[float, LexiconVectorRecord]] = []
        for entry in self._entries:
            if pos_filter is not None and entry.pos not in pos_filter:
                continue
            if not entry.embedding:
                continue
            score = cosine_similarity(query_embedding, entry.embedding)
            if score <= 0:
                continue
            scored.append((score, entry))

        scored.sort(key=lambda item: (-item[0], len(item[1].candidate), item[1].candidate))
        return scored[:limit]

    @staticmethod
    def write_manifest(path: Path, manifest: LexiconVectorIndexManifest) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(manifest.model_dump(), ensure_ascii=True),
            encoding="utf-8",
        )

    def _load(self) -> None:
        if not self._path.is_file():
            return
        payload = json.loads(self._path.read_text(encoding="utf-8"))
        manifest = LexiconVectorIndexManifest.model_validate(payload)
        self._manifest = manifest
        self._entries = manifest.entries


@lru_cache(maxsize=1)
def get_lexicon_vector_index() -> LexiconVectorIndex:
    return LexiconVectorIndex()


def clear_lexicon_vector_index_cache() -> None:
    get_lexicon_vector_index.cache_clear()
