.PHONY: help install install-api install-web dev dev-api dev-web test lint-api typecheck-api build-web db-up db-down clean

PYTHON ?= python3
VENV ?= apps/api/.venv
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
RUFF := $(VENV)/bin/ruff
MYPY := $(VENV)/bin/mypy
UVICORN := $(VENV)/bin/uvicorn

help:
	@echo "Prompt Piper — common tasks"
	@echo ""
	@echo "  make install       Install backend and frontend dependencies"
	@echo "  make dev           Run API and web dev servers (API in background)"
	@echo "  make dev-api       Run FastAPI with reload"
	@echo "  make dev-web       Run Vite dev server"
	@echo "  make test          Run backend and integration tests"
	@echo "  make lint-api      Run ruff on backend"
	@echo "  make typecheck-api Run mypy on backend"
	@echo "  make build-web     Build frontend for production"
	@echo "  make db-up         Start PostgreSQL (Podman)"
	@echo "  make db-down       Stop PostgreSQL (Podman)"
	@echo "  make clean         Remove local build artifacts"

install: install-api install-web

install-api:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e "apps/api[dev]"

install-web:
	npm install

dev:
	@echo "Starting API on :8000 and web on :5173"
	@$(MAKE) dev-api &
	@sleep 2
	@$(MAKE) dev-web

dev-api:
	$(UVICORN) prompt_piper_api.main:app --reload --host 0.0.0.0 --port 8000 --app-dir apps/api/src

dev-web:
	npm run dev:web

test:
	PYTHONPATH=apps/api/src $(PYTEST) tests -q

lint-api:
	$(RUFF) check apps/api/src

typecheck-api:
	PYTHONPATH=apps/api/src $(MYPY) apps/api/src

build-web:
	npm run build:web

db-up:
	podman-compose -f infra/podman-compose.yml up -d

db-down:
	podman-compose -f infra/podman-compose.yml down

clean:
	rm -rf apps/api/.venv apps/api/.pytest_cache apps/api/.mypy_cache apps/api/.ruff_cache
	rm -rf node_modules apps/web/dist apps/web/node_modules packages/shared/node_modules
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
