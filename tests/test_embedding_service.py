from __future__ import annotations

from unittest.mock import MagicMock, patch

from prompt_piper_api.services.embedding_service import (
    SentenceTransformerEmbedder,
    _is_accelerator_error,
)


def test_is_accelerator_error_detects_cuda_messages() -> None:
    assert _is_accelerator_error(RuntimeError("CUDA error: no kernel image")) is True
    assert _is_accelerator_error(ValueError("something else")) is False


def test_sentence_transformer_embedder_retries_on_cpu_after_cuda_failure() -> None:
    vector = MagicMock()
    vector.tolist.return_value = [0.1, 0.2]
    model = MagicMock()
    model.encode.side_effect = [
        RuntimeError("CUDA error: no kernel image is available for execution on the device"),
        [vector],
    ]

    with patch(
        "sentence_transformers.SentenceTransformer",
        return_value=model,
    ) as constructor:
        embedder = SentenceTransformerEmbedder("test-model", device="cuda")
        vectors = embedder.embed(["hello"])

    assert vectors == [[0.1, 0.2]]
    assert embedder.device == "cpu"
    assert constructor.call_count == 2
    constructor.assert_any_call("test-model", device="cuda")
    constructor.assert_any_call("test-model", device="cpu")
    model.encode.assert_any_call(["hello"], normalize_embeddings=True, device="cuda")
    model.encode.assert_any_call(["hello"], normalize_embeddings=True, device="cpu")
