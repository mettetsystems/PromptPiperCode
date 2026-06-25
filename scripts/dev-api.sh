#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${ROOT}/apps/api/.venv/bin"
PYTHON="${VENV}/python"

if [[ ! -x "${VENV}/uvicorn" ]]; then
  echo "API venv missing. Run: make install-api" >&2
  exit 1
fi

cd "${ROOT}"
eval "$("${PYTHON}" -m prompt_piper.setup.ensure_llm --shell)"
# Watch API source only — not data/, logs, or models (reload would wipe in-memory sessions).
exec "${VENV}/uvicorn" prompt_piper_api.main:app --reload \
  --reload-dir "${ROOT}/apps/api/prompt_piper_api" \
  --reload-dir "${ROOT}/apps/api/prompt_piper" \
  --host "${API_HOST:-127.0.0.1}" \
  --port "${API_PORT:-8000}"
