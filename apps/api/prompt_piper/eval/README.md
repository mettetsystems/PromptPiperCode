# Quality eval (`prompt_piper/eval/`)

CLI runner for pre-inference regression cases and quality gate checks.

| Module | Role |
|--------|------|
| `runner.py` | Loads `tests/evals/regression_cases.yaml`, runs pairwise comparisons |
| `__main__.py` | `python -m prompt_piper.eval` entry |

## Run

```bash
# From repo root
make eval
```

Cases live in [`tests/evals/`](../../../tests/evals/README.md). Failures report regression loss rate and gate failures.
