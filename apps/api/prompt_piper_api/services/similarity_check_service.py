from __future__ import annotations

from prompt_piper_api.domain.requirement_card import RequirementCard
from prompt_piper_api.domain.similarity import (
    SIMILARITY_WARNING_MESSAGE,
    SimilarityCheckResult,
    SimilarityMatch,
)
from prompt_piper_api.services.embedding_service import EmbeddingService
from prompt_piper_api.services.hybrid_retrieval_service import HybridRetrievalService
from prompt_piper_api.services.similarity_index_service import (
    SimilarityIndexService,
    build_lessons_learned,
    compress_abstract,
)


class SimilarityCheckService:
    """Run similarity checks on finalize and index retrievable prompt documents."""

    def __init__(
        self,
        embedding: EmbeddingService,
        index: SimilarityIndexService,
        retrieval: HybridRetrievalService,
        *,
        threshold: float = 0.90,
    ) -> None:
        self._embedding = embedding
        self._index = index
        self._retrieval = retrieval
        self._threshold = threshold

    @property
    def threshold(self) -> float:
        return self._threshold

    def check_and_index(
        self,
        *,
        prompt_id: str,
        version: int,
        title: str,
        body: str,
        abstract: str,
        requirement_card: RequirementCard,
        artifact_paths: dict[str, str],
    ) -> SimilarityCheckResult:
        resolved_abstract = compress_abstract(abstract, body)
        lessons = build_lessons_learned(requirement_card)
        texts = [body, resolved_abstract, lessons]
        embeddings = self._embedding.embed(texts)

        matches = self._retrieval.retrieve(
            body,
            embeddings[0],
            exclude_prompt_id=prompt_id,
        )
        warning = self._warning_for_matches(matches)

        self._index.index_prompt(
            prompt_id=prompt_id,
            version=version,
            title=title,
            body=body,
            abstract=abstract,
            requirement_card=requirement_card,
            artifact_paths=artifact_paths,
            embeddings=embeddings,
        )

        return SimilarityCheckResult(warning=warning, matches=matches)

    def _warning_for_matches(self, matches: list[SimilarityMatch]) -> str | None:
        if not matches:
            return None
        top = max(matches, key=lambda match: match.similarity_score)
        if top.similarity_score >= self._threshold:
            return SIMILARITY_WARNING_MESSAGE
        return None
