from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from prompt_piper_api.domain.enums import SessionState
from prompt_piper_api.services.session_service import SessionService
from prompt_piper_api.services.session_store import FileSessionStore


def test_session_persists_across_service_instances(tmp_path: Path) -> None:
    store = FileSessionStore(tmp_path / "sessions")
    service = SessionService(llm=None, store=store)
    created = service.create_session(initial_request="Draft a release note prompt")
    session_id = created.record.session.id

    reloaded = SessionService(llm=None, store=store)
    record = reloaded.get_session(session_id)

    assert record.session.state is SessionState.CLARIFYING
    assert record.pending_clarification is not None
    assert created.clarification_field == record.pending_clarification.field_name


def test_get_session_survives_api_service_restart(client: TestClient) -> None:
    create = client.post("/sessions", json={"initial_request": "Draft a weekly status update prompt"})
    assert create.status_code == 201
    session_id = create.json()["session"]["id"]

    from prompt_piper_api.routes import sessions as sessions_routes

    sessions_routes._session_service = None

    fetched = client.get(f"/sessions/{session_id}")
    assert fetched.status_code == 200
    assert fetched.json()["session"]["id"] == session_id
    assert fetched.json()["session"]["state"] == SessionState.CLARIFYING.value
