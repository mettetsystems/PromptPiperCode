#!/usr/bin/env bash
# Clean shutdown for native API/Vite, managed llama-server, Podman compose, and Quadlets.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

usage() {
  cat <<'EOF'
Stop running Nautilius Prompting Workbench processes on this machine.

Usage:
  ./scripts/shutdown.sh
  make shutdown

Stops, in order:
  1. Native Vite (make dev-web)
  2. Native FastAPI / uvicorn (make dev-api)
  3. Nautilius-managed llama-server (same as make llama-down)
  4. User systemd Quadlets, if they are active
  5. Podman compose stack, if Podman is installed

Does not delete data, disable Quadlets, or skip a later boot start.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

belongs_to_repo() {
  local pid="$1"
  local cwd cmdline
  cwd="$(readlink -f "/proc/${pid}/cwd" 2>/dev/null || true)"
  cmdline="$(tr '\0' ' ' < "/proc/${pid}/cmdline" 2>/dev/null || true)"
  [[ "$cwd" == "$ROOT" || "$cwd" == "$ROOT"/* ]] && return 0
  [[ "$cmdline" == *"$ROOT"* ]] && return 0
  return 1
}

collect_pids() {
  local kind="$1"
  local pid cmdline
  while read -r pid; do
    [[ -z "$pid" || "$pid" == "$$" || "$pid" == "$PPID" ]] && continue
    kill -0 "$pid" 2>/dev/null || continue
    belongs_to_repo "$pid" || continue
    cmdline="$(tr '\0' ' ' < "/proc/${pid}/cmdline" 2>/dev/null || true)"
    case "$kind" in
      api)
        if [[ "$cmdline" == *uvicorn* && "$cmdline" == *prompt_piper_api.main:app* ]]; then
          echo "$pid"
        fi
        ;;
      web)
        if [[ "$cmdline" == *vitest* ]]; then
          continue
        fi
        if [[ "$cmdline" == *vite* ]] || [[ "$cmdline" == *"npm run dev"* ]]; then
          echo "$pid"
        fi
        ;;
    esac
  done < <(pgrep -f 'uvicorn prompt_piper_api.main:app|[v]ite|npm run dev' 2>/dev/null || true)
}

unique_pids() {
  local -A seen=()
  local pid
  for pid in "$@"; do
    [[ -z "$pid" ]] && continue
    [[ -n "${seen[$pid]:-}" ]] && continue
    seen[$pid]=1
    echo "$pid"
  done
}

collect_tree() {
  local pid="$1"
  local child
  echo "$pid"
  while read -r child; do
    [[ -n "$child" ]] && collect_tree "$child"
  done < <(pgrep -P "$pid" 2>/dev/null || true)
}

stop_pids() {
  local label="$1"
  shift
  local pids=()
  local pid
  local expanded=()
  local root_pid child
  for root_pid in "$@"; do
    while read -r child; do
      expanded+=("$child")
    done < <(collect_tree "$root_pid")
  done
  while read -r pid; do
    pids+=("$pid")
  done < <(unique_pids "${expanded[@]+"${expanded[@]}"}")

  if [[ ${#pids[@]} -eq 0 ]]; then
    echo "  ${label}: not running"
    return 0
  fi

  echo "  ${label}: sending SIGTERM to ${pids[*]}"
  kill -TERM "${pids[@]}" 2>/dev/null || true

  local alive
  for _ in {1..32}; do
    alive=()
    for pid in "${pids[@]}"; do
      if kill -0 "$pid" 2>/dev/null; then
        alive+=("$pid")
      fi
    done
    if [[ ${#alive[@]} -eq 0 ]]; then
      echo "  ${label}: stopped"
      return 0
    fi
    pids=("${alive[@]}")
    sleep 0.25
  done

  echo "  ${label}: sending SIGKILL to ${pids[*]}"
  kill -KILL "${pids[@]}" 2>/dev/null || true
  echo "  ${label}: stopped"
}

stop_unit_if_active() {
  local unit="$1"
  if systemctl --user --quiet is-active "$unit" 2>/dev/null; then
    echo "  systemd: stopping ${unit}"
    systemctl --user stop "$unit" || true
  fi
}

echo "Shutting down Nautilius Prompting Workbench..."

mapfile -t WEB_PIDS < <(collect_pids web)
if [[ ${#WEB_PIDS[@]} -gt 0 ]]; then
  stop_pids "Vite" "${WEB_PIDS[@]}"
else
  stop_pids "Vite"
fi

mapfile -t API_PIDS < <(collect_pids api)
if [[ ${#API_PIDS[@]} -gt 0 ]]; then
  stop_pids "API (uvicorn)" "${API_PIDS[@]}"
else
  stop_pids "API (uvicorn)"
fi

PYTHON="${ROOT}/apps/api/.venv/bin/python"
if [[ -x "$PYTHON" ]]; then
  PROMPT_PIPER_REPO_ROOT="${ROOT}" "$PYTHON" -m prompt_piper.setup.ensure_llm --stop || true
else
  echo "  llama-server: API venv missing; skipped"
fi

if command -v systemctl >/dev/null 2>&1; then
  stop_unit_if_active prompt-piper.service
  stop_unit_if_active prompt-piper-web.service
  stop_unit_if_active prompt-piper-api.service
  stop_unit_if_active prompt-piper-postgres.service
  stop_unit_if_active prompt-piper-llama.service
fi

if command -v podman >/dev/null 2>&1; then
  echo "  podman: compose down"
  podman compose -f "${ROOT}/infra/podman-compose.yml" down >/dev/null || true
else
  echo "  podman: not installed"
fi

echo "Shutdown complete."
