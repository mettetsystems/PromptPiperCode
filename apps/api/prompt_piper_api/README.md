# `prompt_piper_api` — HTTP API and core backend

FastAPI application for **PromptPiperCode**: the local-first coding prompt workflow (intake → clarify → edit → finalize → similarity → optimize → approve → export → complete, with optional send-to-model).

Intake fills a nested six-dimension `RequirementCard`. Drafts use six plain-text coding sections. Exports include rendered prompts plus `coding_prompt_spec.json` / `.yaml`.

Post-optimization, **semantic precision** scoring and optional LLM refinement run during the optimization step; **send-to-model** runs after export from the Complete page or via `POST /sessions/{id}/send-to-inference`.

## Layout

| Directory | README | Responsibility |
|-----------|--------|----------------|
| `domain/` | [domain/README.md](domain/README.md) | Pydantic models — sessions, drafts, coding RequirementCard, optimization |
| `routes/` | [routes/README.md](routes/README.md) | REST route handlers (`/sessions`, `/registry`, `/health`) |
| `schemas/` | [schemas/README.md](schemas/README.md) | Request/response DTOs and serializers |
| `services/` | [services/README.md](services/README.md) | Business logic — `SessionService`, registry, similarity, export |
| `llm/` | [llm/README.md](llm/README.md) | OpenAI-compatible client adapters and factory |
| `db/` | [db/README.md](db/README.md) | SQLAlchemy models and DB session (Postgres/pgvector) |
| `api/` | [api/README.md](api/README.md) | Global exception handlers |
| `main.py` | — | FastAPI app factory (title: PromptPiperCode API) and router mount |

## Entry point

```bash
# Typical dev invocation (see apps/api/README.md)
uvicorn prompt_piper_api.main:app --reload --host 127.0.0.1 --port 8000
```

Session orchestration is centralized in `services/session_service.py`; allowed actions per state are in `services/state_transitions.py`.
