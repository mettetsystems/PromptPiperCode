"""Build the precision lexicon vector index."""

from __future__ import annotations

import argparse
from pathlib import Path

from prompt_piper_api.config import get_settings
from prompt_piper_api.services.lexicon_index_builder import build_lexicon_vector_index


def main(argv: list[str] | None = None) -> int:
    settings = get_settings()
    parser = argparse.ArgumentParser(
        description="Embed WordNet + glossary entries for precision vector search.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=settings.lexicon_vector_index_path,
        help="Output JSON path (default: LEXICON_VECTOR_INDEX_PATH)",
    )
    parser.add_argument(
        "--embedding-model",
        default=settings.prompt_piper_embedding_model,
        help="Sentence Transformers model name",
    )
    args = parser.parse_args(argv)

    result = build_lexicon_vector_index(
        args.output,
        embedding_model=args.embedding_model,
    )
    print(
        f"Wrote {result.entry_count} lexicon vectors to {result.output_path} "
        f"using {result.embedding_model}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
