from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from prompt_piper.setup.embedding_device import EmbeddingDeviceDecision
from prompt_piper.setup.lexicon_setup import (
    is_vector_index_built,
    is_wordnet_installed,
    lexicon_dir,
    nltk_data_dir,
    run_lexicon_setup,
    vector_index_path,
)


def test_nltk_paths_under_repo_data(tmp_path: Path) -> None:
    assert nltk_data_dir(tmp_path) == tmp_path / "data" / "nltk_data"
    assert lexicon_dir(tmp_path) == tmp_path / "data" / "lexicon"
    assert vector_index_path(tmp_path) == tmp_path / "data" / "lexicon" / "precision_vectors.json"


def test_is_wordnet_installed_detects_corpus(tmp_path: Path) -> None:
    assert is_wordnet_installed(tmp_path) is False
    (tmp_path / "data" / "nltk_data" / "corpora" / "wordnet").mkdir(parents=True)
    assert is_wordnet_installed(tmp_path) is True


def test_is_vector_index_built_requires_nonempty_file(tmp_path: Path) -> None:
    path = vector_index_path(tmp_path)
    assert is_vector_index_built(tmp_path) is False
    path.parent.mkdir(parents=True)
    path.write_text("{}", encoding="utf-8")
    assert is_vector_index_built(tmp_path) is True


def test_run_lexicon_setup_skips_index_when_present(tmp_path: Path) -> None:
    index = vector_index_path(tmp_path)
    index.parent.mkdir(parents=True)
    index.write_text('{"entries":[]}', encoding="utf-8")
    (tmp_path / "data" / "nltk_data" / "corpora" / "wordnet").mkdir(parents=True)

    with (
        patch("prompt_piper.setup.lexicon_setup.setup_wordnet", return_value=True) as wordnet,
        patch("prompt_piper.setup.lexicon_setup.setup_lexicon_embed", return_value=True) as embed,
        patch("prompt_piper.setup.lexicon_setup.configure_embedding_runtime") as configure,
        patch("prompt_piper.setup.lexicon_setup.build_vector_index") as build,
    ):
        configure.return_value = EmbeddingDeviceDecision("cpu", "test")
        result = run_lexicon_setup(root=tmp_path)

    wordnet.assert_called_once()
    embed.assert_called_once()
    configure.assert_called_once()
    build.assert_not_called()
    assert result.vector_index_ready is True
    assert result.index_build_skipped is True
    assert result.embedding_device == "cpu"


def test_run_lexicon_setup_builds_index_when_missing(tmp_path: Path) -> None:
    built = vector_index_path(tmp_path)

    with (
        patch("prompt_piper.setup.lexicon_setup.setup_wordnet", return_value=True),
        patch("prompt_piper.setup.lexicon_setup.setup_lexicon_embed", return_value=True),
        patch("prompt_piper.setup.lexicon_setup.configure_embedding_runtime") as configure,
        patch(
            "prompt_piper.setup.lexicon_setup.build_vector_index",
            return_value=built,
        ) as build,
        patch(
            "prompt_piper.setup.lexicon_setup.is_vector_index_built",
            side_effect=[False, True],
        ),
    ):
        configure.return_value = EmbeddingDeviceDecision("cpu", "test")
        result = run_lexicon_setup(root=tmp_path)

    build.assert_called_once_with(tmp_path, force=False)
    assert result.vector_index_ready is True
    assert result.index_build_skipped is False
