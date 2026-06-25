# Integration tests (`tests/integration/`)

Lightweight checks that the assembled FastAPI app starts and exposes expected routes.

| File | Role |
|------|------|
| `test_api_startup.py` | Import `app`, hit `/health` |

Run as part of `make test` — no separate marker required.
