#!/usr/bin/env bash
# Stop the Prompt Piper Podman stack.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

podman compose -f infra/podman-compose.yml down

echo "Prompt Piper containers stopped."
