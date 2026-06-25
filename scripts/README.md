# Scripts (`scripts/`)

Bash helpers invoked by `Makefile` targets. Run from repo root unless noted.

| Script | Make target | Purpose |
|--------|-------------|---------|
| `setup.sh` | `make setup` | Run `prompt_piper.setup` wizard |
| `dev-api.sh` | `make dev-api` | `ensure_llm` + uvicorn with reload on API dirs only |
| `ensure-llm.sh` | `make ensure-llm` | GPU probe and llama-server start |
| `dev-up.sh` | `make podman-up` | Create export dirs, `podman compose up` |
| `dev-down.sh` | `make podman-down` | Stop compose stack |
| `dev-logs.sh` | `make podman-logs` | Follow service logs (`api`, `web`, `postgres`, …) |
| `init-db.sh` | `make podman-init-db` | Verify pgvector and app tables |
| `init-db-quadlet.sh` | — | DB init variant for Quadlet deployments |
| `install-quadlets.sh` | — | Install user systemd Quadlet units |

```bash
# Example: start native API with auto-LLM
./scripts/dev-api.sh

# Example: tail API container logs
./scripts/dev-logs.sh api
```

All scripts use `set -euo pipefail` and resolve repo root relative to their own path.
