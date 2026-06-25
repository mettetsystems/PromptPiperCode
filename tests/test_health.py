def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "prompt-piper-api"
    assert "version" in payload
    assert "timestamp" in payload
    assert payload["database"] in {"sqlite", "postgresql"}
