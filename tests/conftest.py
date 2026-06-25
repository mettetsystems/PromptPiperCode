"""Shared pytest fixtures for Prompt Piper tests."""

import pytest
from fastapi.testclient import TestClient

from prompt_piper_api.config import get_settings
from prompt_piper_api.main import create_app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("APP_DEBUG", "false")
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    get_settings.cache_clear()

    import prompt_piper_api.db.session as session_module

    session_module._engine = None

    app = create_app()

    with TestClient(app) as test_client:
        yield test_client

    get_settings.cache_clear()
    session_module._engine = None
