#!/usr/bin/env bash
# Install PromptPiperCode Quadlet units for rootless Podman (Fedora).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
QUADLET_SRC="${ROOT}/infra/quadlets"
QUADLET_DEST="${HOME}/.config/containers/systemd"
METHOD="compose"

usage() {
  cat <<EOF
Usage: $(basename "$0") [--method compose|containers]

Install PromptPiperCode Quadlet units into:
  ${QUADLET_DEST}

Methods:
  compose     Install prompt-piper.compose (recommended; uses podman-compose.yml)
  containers  Install .network + postgres + api + web container units

After install:
  loginctl enable-linger "\$USER"    # start at boot without login
  systemctl --user daemon-reload
  systemctl --user enable --now prompt-piper.service   # compose method
  # or enable individual units — see infra/quadlets/README.md
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --method)
      METHOD="${2:-}"
      shift 2
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if ! command -v podman >/dev/null 2>&1; then
  echo "error: podman is not installed. On Fedora: sudo dnf install podman podman-compose" >&2
  exit 1
fi

mkdir -p \
  "${HOME}/Documents/PromptPiperCode/exports" \
  "${HOME}/Documents/PromptPiperCode/registry" \
  "${HOME}/Documents/PromptPiperCode/audit" \
  "${ROOT}/data/postgres" \
  "${ROOT}/data/model-cache" \
  "${ROOT}/data/nltk_data" \
  "${ROOT}/data/lexicon" \
  "${QUADLET_DEST}"

if [[ ! -f "${ROOT}/.env" ]]; then
  cp "${ROOT}/.env.example" "${ROOT}/.env"
  echo "Created ${ROOT}/.env from .env.example"
fi

if [[ -x "${ROOT}/apps/api/.venv/bin/python" ]]; then
  echo "Ensuring precision lexicon data (WordNet + embeddings)..."
  "${ROOT}/scripts/setup-lexicon.sh" --skip-index || true
fi

mkdir -p "${QUADLET_DEST}"

case "${METHOD}" in
  compose)
    cp "${QUADLET_SRC}/prompt-piper.compose" "${QUADLET_DEST}/"
    echo "Installed compose Quadlet: ${QUADLET_DEST}/prompt-piper.compose"
    echo "Generates user unit: prompt-piper.service"
    ;;
  containers)
    cp \
      "${QUADLET_SRC}/prompt-piper.network" \
      "${QUADLET_SRC}/prompt-piper-postgres.container" \
      "${QUADLET_SRC}/prompt-piper-api.container" \
      "${QUADLET_SRC}/prompt-piper-web.container" \
      "${QUADLET_DEST}/"
    echo "Installed container Quadlets in ${QUADLET_DEST}/"
    echo "Units: prompt-piper-network, prompt-piper-postgres, prompt-piper-api, prompt-piper-web"
    ;;
  *)
    echo "error: --method must be 'compose' or 'containers'" >&2
    exit 1
    ;;
esac

cat <<EOF

Next steps:

1. Enable linger (required for boot-time start without logging in):
     loginctl enable-linger "\$USER"

2. Build container images (once, or after code changes):
EOF

if [[ "${METHOD}" == "compose" ]]; then
  cat <<EOF
     cd ${ROOT}
     podman compose -f infra/podman-compose.yml build
EOF
else
  cat <<EOF
     cd ${ROOT}
     podman build -f infra/Containerfile.api -t localhost/prompt-piper-api:latest .
     podman build -f infra/Containerfile.web \\
       --build-arg VITE_API_BASE_URL=http://127.0.0.1:8000 \\
       -t localhost/prompt-piper-web:latest .
EOF
fi

cat <<EOF

3. Reload systemd user units:
     systemctl --user daemon-reload

4. Enable and start:
EOF

if [[ "${METHOD}" == "compose" ]]; then
  cat <<EOF
     systemctl --user enable --now prompt-piper.service
     ${ROOT}/scripts/init-db.sh
EOF
else
  cat <<EOF
     systemctl --user enable --now prompt-piper-network.service
     systemctl --user enable --now prompt-piper-postgres.service
     systemctl --user enable --now prompt-piper-api.service
     systemctl --user enable --now prompt-piper-web.service
     ${ROOT}/scripts/init-db-quadlet.sh
EOF
fi

cat <<EOF

5. Precision lexicon (host, once per machine):
     make setup-lexicon-all
     # Or skip the long index build: make setup-lexicon && make setup-lexicon-embed

6. Verify:
     curl http://127.0.0.1:8000/health
     # Web UI: http://127.0.0.1:5173

Full guide: ${ROOT}/infra/quadlets/README.md
EOF
