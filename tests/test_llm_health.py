from fastapi.testclient import TestClient

from prompt_piper_api.main import app


def test_llm_health_disabled(monkeypatch) -> None:
    monkeypatch.setenv("PROMPT_PIPER_LLM_ENABLED", "false")
    from prompt_piper_api.config import get_settings

    get_settings.cache_clear()

    client = TestClient(app)
    response = client.get("/health/llm")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "disabled"
    assert body["llm_enabled"] is False
