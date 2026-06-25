from __future__ import annotations

from typing import Protocol

from prompt_piper_api.services.similarity_utils import hash_embed


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class HashFallbackEmbedder:
    """Deterministic embedding fallback when Sentence Transformers is unavailable."""

    def __init__(self, dimensions: int = 384) -> None:
        self._dimensions = dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [hash_embed(text, dimensions=self._dimensions) for text in texts]


def _is_accelerator_error(exc: BaseException) -> bool:
    message = str(exc).lower()
    if "cuda" in message or "accelerator" in message:
        return True
    name = type(exc).__name__.lower()
    return "cuda" in name or "accelerator" in name


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str, *, device: str = "cpu") -> None:
        from sentence_transformers import SentenceTransformer

        self._model_name = model_name
        self._device = device
        self._model = SentenceTransformer(model_name, device=device)

    @property
    def device(self) -> str:
        return self._device

    def embed(self, texts: list[str]) -> list[list[float]]:
        try:
            return self._encode(texts, self._device)
        except Exception as exc:
            if self._device != "cpu" and _is_accelerator_error(exc):
                self._switch_to_cpu()
                return self._encode(texts, "cpu")
            raise

    def _encode(self, texts: list[str], device: str) -> list[list[float]]:
        vectors = self._model.encode(texts, normalize_embeddings=True, device=device)
        return [vector.tolist() for vector in vectors]

    def _switch_to_cpu(self) -> None:
        from sentence_transformers import SentenceTransformer

        self._device = "cpu"
        self._model = SentenceTransformer(self._model_name, device="cpu")


class EmbeddingService:
    """Local embedding service with Sentence Transformers and deterministic fallback."""

    DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"
    DEFAULT_DEVICE = "cpu"

    def __init__(
        self,
        *,
        model_name: str = DEFAULT_MODEL,
        embedder: Embedder | None = None,
        prefer_fallback: bool = False,
        device: str | None = None,
    ) -> None:
        self._model_name = model_name
        self._prefer_fallback = prefer_fallback
        self._device = device
        self._embedder = embedder or self._load_embedder()

    @property
    def using_fallback(self) -> bool:
        return isinstance(self._embedder, HashFallbackEmbedder)

    @property
    def model_name(self) -> str:
        if self.using_fallback:
            return "hash-fallback"
        return self._model_name

    @property
    def device(self) -> str:
        if isinstance(self._embedder, SentenceTransformerEmbedder):
            return self._embedder.device
        if self.using_fallback:
            return "hash-fallback"
        return self._resolve_device()

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return self._embedder.embed(texts)

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]

    def _resolve_device(self) -> str:
        if self._device is not None:
            return self._device
        from prompt_piper_api.config import get_settings

        return get_settings().prompt_piper_embedding_device

    def _load_embedder(self) -> Embedder:
        if self._prefer_fallback:
            return HashFallbackEmbedder()
        try:
            return SentenceTransformerEmbedder(
                self._model_name,
                device=self._resolve_device(),
            )
        except Exception:
            return HashFallbackEmbedder()
