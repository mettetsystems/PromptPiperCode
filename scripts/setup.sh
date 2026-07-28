#!/usr/bin/env bash
# Interactive PromptPiperCode setup wizard (model / CPU-only configuration).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example."
fi

API_DIR="${ROOT}/apps/api"
VENV="${API_DIR}/.venv"
PYTHON="${VENV}/bin/python"

if [[ ! -x "${PYTHON}" ]]; then
  echo "Backend venv not found. Run 'make install-api' first, then 'make setup'." >&2
  exit 1
fi

"${PYTHON}" -m prompt_piper.setup "$@"
setup_status=$?

if [[ "${setup_status}" -ne 0 ]]; then
  exit "${setup_status}"
fi

echo ""
echo "Setting up precision lexicon (WordNet + embeddings)..."
if [[ -f "${ROOT}/data/lexicon/precision_vectors.json" ]]; then
  "${ROOT}/scripts/setup-lexicon.sh" --skip-index
else
  if [[ -t 0 ]]; then
    read -r -p "Build semantic vector index now (~20–60 min CPU)? [y/N] " build_index || build_index=""
    if [[ "${build_index}" == "y" || "${build_index}" == "Y" ]]; then
      "${ROOT}/scripts/setup-lexicon.sh"
    else
      "${ROOT}/scripts/setup-lexicon.sh" --skip-index
      echo "Run 'make build-lexicon-index' later for semantic vector ranking."
    fi
  else
    "${ROOT}/scripts/setup-lexicon.sh" --skip-index
    echo "Run 'make build-lexicon-index' for semantic vector ranking."
  fi
fi
