from __future__ import annotations

from fastapi.testclient import TestClient
from prompt_piper_api.domain.enums import SessionState
from prompt_piper_api.domain.limits import MAX_CLARIFICATION_QUESTIONS
from prompt_piper_api.services.clarification_flow import drive_session_to_edit

__all__ = ["drive_client_session_to_edit", "drive_session_to_edit"]


def drive_client_session_to_edit(
    client: TestClient,
    session_id: str,
    *,
    answers: list[str] | None = None,
) -> dict:
    """Answer clarifications via HTTP until the session reaches edit state."""
    response: dict | None = None
    if answers:
        for answer in answers:
            result = client.post(f"/sessions/{session_id}/answer", json={"answer": answer})
            assert result.status_code == 200
            response = result.json()
            if response["session"]["state"] == SessionState.EDIT:
                return response

    for _ in range(MAX_CLARIFICATION_QUESTIONS):
        fetched = client.get(f"/sessions/{session_id}")
        assert fetched.status_code == 200
        payload = fetched.json()
        if payload["session"]["state"] == SessionState.EDIT:
            return payload
        if payload.get("clarification_can_finish"):
            complete = client.post(f"/sessions/{session_id}/clarify/complete")
            assert complete.status_code == 200
            return complete.json()
        result = client.post(f"/sessions/{session_id}/answer", json={"answer": "unspecified"})
        assert result.status_code == 200
        response = result.json()
        if response["session"]["state"] == SessionState.EDIT:
            return response

    complete = client.post(f"/sessions/{session_id}/clarify/complete")
    assert complete.status_code == 200
    return complete.json()
