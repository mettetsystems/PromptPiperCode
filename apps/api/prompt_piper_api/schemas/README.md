# API schemas (`schemas/`)

Pydantic models for HTTP request bodies and responses. Map domain objects via `to_session_response()` / `to_session_detail()` in `session.py`.

| Module | Purpose |
|--------|---------|
| `session.py` | `CreateSessionRequest`, `SessionDetailResponse`, clarification and edit payloads |
| `precision.py` | Precision review, suggest, and apply request/response DTOs |
| `registry.py` | Registry list and detail responses |
| `health.py` | Health and LLM status JSON |
| `inference.py` | Send-to-inference request/response and inference settings |

Schemas stay separate from `domain/` so API evolution (field naming, optional enrichment) does not leak into the session aggregate.
