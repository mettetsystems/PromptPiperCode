# Local setup

PromptPiperCode local development and Podman deployment.

## Prerequisites

- Python 3.12+
- Node.js 20+ and npm
- Make
- Podman (optional, for PostgreSQL with pgvector)

## Quick start

```bash
cp .env.example .env
make install
make setup      # optional: CPU-only or local SLM wizard
make dev-api    # terminal 1
make dev-web    # terminal 2
```

- API: http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs
- Web: http://127.0.0.1:5173

## Environment

Copy `.env.example` to `.env` at the repo root. Key variables:

| Variable           | Default                              | Description                    |
|--------------------|--------------------------------------|--------------------------------|
| `DATABASE_URL`     | `sqlite:///./data/prompt_piper.db`   | SQLite or PostgreSQL URL       |
| `REGISTRY_PATH`    | `./data/registry`                    | Git-backed prompt storage      |
| `ARTIFACTS_PATH`   | `./data/artifacts`                   | Generated export files         |
| `VITE_API_BASE_URL`| `http://127.0.0.1:8000`              | Frontend → API base URL        |

### Local model wizard

After `make install`, run the interactive setup wizard:

```bash
make setup
```

Choices:

1. **CPU-only** — disables the chat LLM (`PROMPT_PIPER_LLM_ENABLED=false`); clarification uses rule-based fallbacks.
2. **Gemma 3** — official `google/*-qat-q4_0-gguf` releases (1B, 4B, 12B prosumer). Requires Hugging Face Gemma license (`hf auth login`).
3. **Gemma 3n** — efficient E4B (~3–4B class); community GGUF from official `google/gemma-3n-E4B-it` weights until Google publishes QAT GGUF.
4. **Qwen3** — official `Qwen/Qwen3-*-GGUF` releases (0.6B–8B). No Gemma license.
5. **Other** — your own OpenAI-compatible URL (vLLM, Ollama, etc.).

The wizard detects GPU VRAM when available and groups presets:

| Tier | VRAM guide | Examples |
|------|------------|----------|
| Compact | ~2–4GB | Qwen3 0.6B/1.7B, Gemma 3 1B |
| Standard (~3–4B class) | ~8GB+ | Qwen3 4B, Gemma 3 4B, Gemma 3n E4B |
| Prosumer (~8B+) | ~16GB+ (4090/5080/5090 class) | Qwen3 8B, Gemma 3 12B |

Non-interactive (CI/scripted):

```bash
./scripts/setup.sh --non-interactive cpu-only
./scripts/setup.sh --non-interactive gemma3-1b
./scripts/setup.sh --non-interactive qwen3-4b
./scripts/setup.sh --non-interactive qwen3-8b
./scripts/setup.sh --non-interactive gemma3-12b
./scripts/setup.sh --non-interactive gemma3n-e4b
./scripts/setup.sh --non-interactive podman:qwen3-1.7b
# legacy aliases still work: qwen3-1.5b, qwen3-3b, gemma3-3b
```

When you pick a Gemma 3 or Qwen3 preset, the wizard also writes Hugging Face CLI install
commands into `.env` and prints them at the end of setup.

Install the download CLI manually (or use the Make target):

```bash
make setup-model-deps
# equivalent: apps/api/.venv/bin/pip install "huggingface_hub[cli]"
hf auth login   # optional; gated models only
```

Then download the GGUF file the wizard printed, for example:

```bash
mkdir -p data/models
hf auth login   # required for official Google Gemma repos
hf download google/gemma-3-1b-it-qat-q4_0-gguf \
  gemma-3-1b-it-q4_0.gguf --local-dir data/models
```

## PostgreSQL (optional)

Start PostgreSQL with pgvector:

```bash
make podman-up
```

Then set in `.env`:

```
DATABASE_URL=postgresql+psycopg://prompt_piper:prompt_piper@localhost:5432/prompt_piper
```

## Development commands

```bash
make test       # pytest
make lint       # ruff check
make typecheck  # mypy
make format     # ruff format + fix
```

## Manual backend setup

```bash
cd apps/api
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn prompt_piper_api.main:app --reload
```

## Manual frontend setup

```bash
cd apps/web
npm install
npm run dev
```

## Container builds (Podman)

Full local stack:

```bash
./scripts/dev-up.sh
```

See [README](../README.md#podman-setup-local-first-no-cloud) for Fedora setup, volumes, and troubleshooting.

Postgres only:

```bash
podman compose -f infra/compose.yaml up -d
./scripts/init-db.sh   # after full stack is up; for postgres-only, run psql manually
```

Manual image builds:

```bash
podman build -f infra/Containerfile.api -t prompt-piper-api .
podman build -f infra/Containerfile.web -t prompt-piper-web .
```

Container environment reference: `infra/env.podman.example`.
