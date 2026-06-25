#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${ROOT}/apps/api/.venv/bin/python"
exec "$PYTHON" -m prompt_piper.setup.ensure_llm "$@"
