# API utilities (`api/`)

Cross-cutting HTTP concerns, not route definitions (those live in `routes/`).

| Module | Role |
|--------|------|
| `exception_handlers.py` | Maps `StateTransitionError`, `ExternalInferenceBlockedError`, `SessionNotFoundError`, etc. to structured JSON (403, 404, 409, …) |

Registered from `main.py` on the FastAPI app instance.
