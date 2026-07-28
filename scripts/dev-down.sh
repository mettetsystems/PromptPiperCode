#!/usr/bin/env bash
# Stop the PromptPiperCode Podman stack.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

podman compose -f infra/podman-compose.yml down

echo "PromptPiperCode containers stopped."
