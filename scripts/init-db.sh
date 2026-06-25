#!/usr/bin/env bash
# Wait for PostgreSQL, ensure pgvector is enabled, and create application tables.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

COMPOSE=(podman compose -f infra/podman-compose.yml)

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

POSTGRES_USER="${POSTGRES_USER:-prompt_piper}"
POSTGRES_DB="${POSTGRES_DB:-prompt_piper}"

echo "Waiting for PostgreSQL..."
ready=0
for _ in $(seq 1 60); do
  if "${COMPOSE[@]}" exec -T postgres pg_isready -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 1
done

if [[ "${ready}" -ne 1 ]]; then
  echo "error: PostgreSQL did not become ready in time." >&2
  exit 1
fi

echo "Ensuring pgvector extension..."
"${COMPOSE[@]}" exec -T postgres \
  psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -v ON_ERROR_STOP=1 \
  -c "CREATE EXTENSION IF NOT EXISTS vector;"

echo "Creating application tables..."
"${COMPOSE[@]}" exec -T api python -c "from prompt_piper_api.db import init_db; init_db()"

echo "Database initialization complete."
