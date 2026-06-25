# Local Setup

This guide covers running Prompt Piper on your machine for development.

## Prerequisites

- Python 3.12+
- Node.js 20+
- npm (workspaces)
- Optional: Podman for containerized PostgreSQL
- Optional: PostgreSQL 16+ with pgvector for production-like local dev

## Quick start

```bash
cp .env.example .env
make install
make dev
```

This starts:

- API at `http://localhost:8000`
- Web at `http://localhost:5173`

Verify the API:

```bash
curl http://localhost:8000/health
```

## Backend only

```bash
make install-api
make dev-api
```

The API uses SQLite by default (`DATABASE_URL=sqlite:///./data/prompt_piper.db`).

## Frontend only

```bash
make install-web
make dev-web
```

Set `VITE_API_BASE_URL` in `.env` if the API runs on a non-default host or port.

## PostgreSQL with pgvector (optional)

Start the database with Podman:

```bash
make db-up
```

Then update `.env`:

```env
DATABASE_URL=postgresql+psycopg://prompt_piper:prompt_piper@localhost:5432/prompt_piper
```

Restart the API after changing the database URL.

## Common tasks

| Task            | Command           |
|----------------|-------------------|
| Install all    | `make install`    |
| Run dev stack  | `make dev`        |
| Run tests      | `make test`       |
| Lint backend   | `make lint-api`   |
| Type-check API | `make typecheck-api` |
| Build web      | `make build-web`  |

## Project data directories

- `data/registry` — Git-backed prompt registry (versioned prompt definitions)
- `data/artifacts` — generated exports (ignored by Git except placeholders)

Initialize the registry as its own Git repo when you begin storing prompts:

```bash
cd data/registry
git init
```

## Troubleshooting

**API health check fails from the web app**

- Confirm the API is running: `curl http://localhost:8000/health`
- Confirm `VITE_API_BASE_URL` and `CORS_ORIGINS` in `.env`

**SQLite database locked**

- Ensure only one API process is writing to the same SQLite file.

**PostgreSQL connection errors**

- Run `make db-up` and confirm credentials match `.env`.
