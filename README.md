# Prompt Piper

**Prompt Piper** is a local-first prompt engineering workbench. Design, clarify, edit, finalize, optimize, store, and retrieve prompts on your machine. Only a finalized, user-approved prompt may be sent to an external model — and only when you explicitly choose to.

This repository is a monorepo scaffold. It provides repeatable local development, clean boundaries, and room to grow — not the full product yet.

## Repository structure

```
apps/
  api/                 FastAPI backend (Python 3.12+)
  web/                 React + Vite + TypeScript frontend
packages/
  shared/              Shared TypeScript types
data/
  registry/            Git-backed prompt registry
  artifacts/           Generated TXT, Markdown, HTML, PDF, bibliography outputs
infra/                 Podman Containerfiles and compose manifests
docs/                  Architecture, setup, privacy, registry format
tests/                 Backend and integration tests
```

## Prerequisites

- Python 3.12+
- Node.js 20+
- npm
- Optional: Podman (for PostgreSQL with pgvector)

## Quick start

```bash
cp .env.example .env
make install
make dev
```

Open the web shell at [http://localhost:5173](http://localhost:5173).

Verify the API:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "Prompt Piper",
  "version": "0.1.0",
  "environment": "development",
  "database": "sqlite",
  "timestamp": "..."
}
```

## Development tasks

| Task | Command |
|------|---------|
| Install dependencies | `make install` |
| Run API + web | `make dev` |
| Run API only | `make dev-api` |
| Run web only | `make dev-web` |
| Run tests | `make test` |
| Lint API | `make lint-api` |
| Type-check API | `make typecheck-api` |
| Build web | `make build-web` |
| Start PostgreSQL | `make db-up` |

## Configuration

Copy `.env.example` to `.env` and adjust as needed.

- **SQLite (default)** — zero-setup local development
- **PostgreSQL + pgvector** — set `DATABASE_URL` and run `make db-up`

See [docs/local-setup.md](docs/local-setup.md) for details.

## Documentation

- [Architecture](docs/architecture.md)
- [Local setup](docs/local-setup.md)
- [Privacy model](docs/privacy-model.md)
- [Registry format](docs/registry-format.md)

## Tech stack

**Backend:** FastAPI, Pydantic v2, SQLModel, pytest, ruff, mypy

**Frontend:** React, TypeScript, Vite, TanStack Query

**Infrastructure:** Podman (optional PostgreSQL via pgvector image)

## What is intentionally not included yet

- Prompt authoring workflows
- Registry CRUD APIs
- Artifact generation
- External model dispatch
- pgvector embedding search

The scaffold focuses on structure, naming, and repeatable local development.

## License

TBD
