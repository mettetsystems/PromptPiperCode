# HTTP routes (`routes/`)

Thin FastAPI routers — validate input, call `SessionService` or browse services, return schemas.

| Module | Prefix | Endpoints |
|--------|--------|-----------|
| `sessions.py` | `/sessions` | Create session, get/delete session, clarify, edit, finalize, optimize, approve, precision, artifacts, send-to-inference, workflow re-open, template |
| `registry.py` | `/registry` | List prompts, prompt detail, artifact file download |
| `health.py` | `/health` | API and LLM health probes |
| `settings.py` | `/settings` | Read-only runtime settings (including inference availability) |

Dependency injection: `get_session_service()` in `sessions.py` wires registry, similarity, optimizer, file session store, and audit log from `config.get_settings()`.
