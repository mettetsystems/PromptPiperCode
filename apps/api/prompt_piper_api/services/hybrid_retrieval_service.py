from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine

from prompt_piper_api.domain.similarity import SimilarityMatch
from prompt_piper_api.services.mmr import maximal_marginal_relevance
from prompt_piper_api.services.similarity_index_service import (
    IndexedDocument,
    SimilarityIndexService,
)
from prompt_piper_api.services.similarity_utils import cosine_similarity, short_delta
from prompt_piper_api.services.user_settings_service import UserSettingsService, get_user_settings_service


class HybridRetrievalService:
    """Combine lexical candidate retrieval with vector ranking and MMR diversification."""

    def __init__(
        self,
        index: SimilarityIndexService,
        *,
        engine: Engine | None = None,
        pgvector_enabled: bool = False,
        candidate_limit: int = 50,
        result_limit: int = 5,
        user_settings: UserSettingsService | None = None,
    ) -> None:
        self._index = index
        self._engine = engine
        self._pgvector_enabled = pgvector_enabled
        self._candidate_limit = candidate_limit
        self._result_limit = result_limit
        self._user_settings = user_settings or get_user_settings_service()

    def retrieve(
        self,
        query_text: str,
        query_embedding: list[float],
        *,
        exclude_prompt_id: str | None = None,
    ) -> list[SimilarityMatch]:
        documents = self._candidate_documents(
            query_text,
            exclude_prompt_id=exclude_prompt_id,
            min_indexed_at=self._user_settings.similarity_min_indexed_at(),
        )
        if not documents:
            return []

        if self._pgvector_enabled and self._engine is not None:
            scored = self._score_with_pgvector(query_embedding, documents)
        else:
            scored = self._score_with_cosine(query_embedding, documents)

        collapsed = self._collapse_by_prompt(scored)
        selected = self._apply_mmr(query_embedding, collapsed, query_text=query_text)
        return selected[: self._result_limit]

    def _candidate_documents(
        self,
        query_text: str,
        *,
        exclude_prompt_id: str | None,
        min_indexed_at,
    ) -> list[IndexedDocument]:
        candidate_ids = self._index.lexical_candidate_prompt_ids(
            query_text,
            limit=self._candidate_limit,
        )
        documents = self._index.list_documents(
            exclude_prompt_id=exclude_prompt_id,
            min_indexed_at=min_indexed_at,
        )
        if not candidate_ids:
            return documents
        allowed = set(candidate_ids)
        filtered = [document for document in documents if document.prompt_id in allowed]
        return filtered or documents

    def _score_with_cosine(
        self,
        query_embedding: list[float],
        documents: list[IndexedDocument],
    ) -> list[tuple[IndexedDocument, float]]:
        scored = [
            (document, cosine_similarity(query_embedding, document.embedding))
            for document in documents
        ]
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored

    def _score_with_pgvector(
        self,
        query_embedding: list[float],
        documents: list[IndexedDocument],
    ) -> list[tuple[IndexedDocument, float]]:
        if self._engine is None:
            return self._score_with_cosine(query_embedding, documents)

        prompt_ids = sorted({document.prompt_id for document in documents})
        vector_literal = "[" + ",".join(str(value) for value in query_embedding) + "]"
        sql = text(
            """
            SELECT prompt_id, document_kind,
                   1 - (embedding <=> CAST(:query_embedding AS vector)) AS score
            FROM similarity_documents
            WHERE prompt_id = ANY(:prompt_ids)
            ORDER BY embedding <=> CAST(:query_embedding AS vector)
            LIMIT :limit
            """
        )
        with self._engine.connect() as connection:
            rows = connection.execute(
                sql,
                {
                    "query_embedding": vector_literal,
                    "prompt_ids": prompt_ids,
                    "limit": self._candidate_limit,
                },
            ).fetchall()

        score_by_key = {
            (str(row.prompt_id), str(row.document_kind)): max(0.0, min(1.0, float(row.score)))
            for row in rows
        }
        scored = [
            (
                document,
                score_by_key.get(
                    (document.prompt_id, document.document_kind.value),
                    cosine_similarity(query_embedding, document.embedding),
                ),
            )
            for document in documents
        ]
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored

    def _collapse_by_prompt(
        self,
        scored: list[tuple[IndexedDocument, float]],
    ) -> list[tuple[IndexedDocument, float]]:
        best: dict[str, tuple[IndexedDocument, float]] = {}
        for document, score in scored:
            current = best.get(document.prompt_id)
            if current is None or score > current[1]:
                best[document.prompt_id] = (document, score)
        collapsed = list(best.values())
        collapsed.sort(key=lambda item: item[1], reverse=True)
        return collapsed

    def _apply_mmr(
        self,
        query_embedding: list[float],
        collapsed: list[tuple[IndexedDocument, float]],
        *,
        query_text: str,
    ) -> list[SimilarityMatch]:
        if not collapsed:
            return []

        candidates = [
            (index, document.embedding) for index, (document, _score) in enumerate(collapsed)
        ]
        selected_indices = maximal_marginal_relevance(
            query_embedding,
            candidates,
            top_k=min(self._result_limit, len(candidates)),
        )

        matches: list[SimilarityMatch] = []
        for index in selected_indices:
            document, score = collapsed[index]
            matches.append(
                SimilarityMatch(
                    prompt_id=document.prompt_id,
                    title=document.title,
                    similarity_score=score,
                    artifact_paths=document.artifact_paths,
                    delta=short_delta(query_text, document.text),
                    document_kind=document.document_kind,
                )
            )
        return matches
