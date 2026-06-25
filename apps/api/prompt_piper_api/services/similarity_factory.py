from __future__ import annotations

from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import Engine

from prompt_piper_api.config import Settings
from prompt_piper_api.db.session import engine as default_engine
from prompt_piper_api.services.embedding_service import EmbeddingService
from prompt_piper_api.services.hybrid_retrieval_service import HybridRetrievalService
from prompt_piper_api.services.similarity_check_service import SimilarityCheckService
from prompt_piper_api.services.similarity_index_service import (
    DatabaseSimilarityIndexStore,
    JsonSimilarityIndexStore,
    SimilarityIndexService,
    SimilarityIndexStore,
)


def pgvector_enabled(engine: Engine) -> bool:
    try:
        with engine.connect() as connection:
            row = connection.execute(
                text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            ).first()
            return row is not None
    except Exception:
        return False


def create_similarity_index_store(
    settings: Settings,
    engine: Engine | None = None,
) -> SimilarityIndexStore:
    if settings.similarity_index_path is not None:
        return JsonSimilarityIndexStore(settings.similarity_index_path)
    active_engine = engine or default_engine
    return DatabaseSimilarityIndexStore(
        active_engine,
        use_postgres_fts=not settings.is_sqlite,
    )


def create_similarity_check_service(
    settings: Settings,
    *,
    engine: Engine | None = None,
    index_path: Path | None = None,
    embedding: EmbeddingService | None = None,
) -> SimilarityCheckService:
    active_engine = engine or default_engine
    store: SimilarityIndexStore
    if index_path is not None:
        store = JsonSimilarityIndexStore(index_path)
    elif settings.similarity_index_path is not None:
        store = JsonSimilarityIndexStore(settings.similarity_index_path)
    else:
        store = DatabaseSimilarityIndexStore(
            active_engine,
            use_postgres_fts=not settings.is_sqlite,
        )

    embedder = embedding or EmbeddingService(
        model_name=settings.prompt_piper_embedding_model,
        prefer_fallback=settings.prompt_piper_embedding_fallback,
    )
    index = SimilarityIndexService(store)
    retrieval = HybridRetrievalService(
        index,
        engine=None if settings.is_sqlite else active_engine,
        pgvector_enabled=False if settings.is_sqlite else pgvector_enabled(active_engine),
    )
    return SimilarityCheckService(
        embedder,
        index,
        retrieval,
        threshold=settings.similarity_warning_threshold,
    )
