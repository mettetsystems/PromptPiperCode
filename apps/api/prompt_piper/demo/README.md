# Demo runner (`prompt_piper/demo/`)

Runs a scripted session through clarify → edit → finalize → optimize → export using the implementation-report scenario.

| Module | Role |
|--------|------|
| `scenario.py` | Prints step-by-step progress |
| `runner.py` | Drives `SessionService` with fixed answers |
| `__main__.py` | `python -m prompt_piper.demo` entry |

## Run

```bash
# From repo root
make demo
```

Uses isolated paths under `data/demo/` when configured in the demo flow tests.
