# Prompt Piper API

FastAPI backend for the Prompt Piper local-first prompt engineering workbench.

## Local development

From the repository root:

```bash
make install-api
make dev-api
```

Or from this directory:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn prompt_piper_api.main:app --reload --host 0.0.0.0 --port 8000
```

Health check: `GET http://localhost:8000/health`
