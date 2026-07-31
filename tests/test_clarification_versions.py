from __future__ import annotations

import json

from fastapi.testclient import TestClient

from prompt_piper_api.domain.requirement_card import RequirementCard
from prompt_piper_api.domain.user_settings import ClarificationVersionsAvailable
from prompt_piper_api.llm.base import ChatMessage
from prompt_piper_api.llm.mock import MockLLMClient
from prompt_piper_api.services.ask_the_locals_service import (
    AskTheLocalsService,
    collect_previous_answers,
)
from prompt_piper_api.services.clarification_option_guides import (
    assert_guides_cover_all_options,
    build_quick_reply_guides,
)
from prompt_piper_api.services.clarification_prompts import (
    ADVANCED_PROMPTS,
    BEGINNER_PROMPTS,
    ClarificationLevel,
    STANDARD_PROMPTS,
    build_version_texts,
)
from prompt_piper_api.services.clarification_question_ranker import ClarificationQuestionRanker


def test_prompt_maps_cover_same_fields() -> None:
    assert set(STANDARD_PROMPTS) == set(BEGINNER_PROMPTS) == set(ADVANCED_PROMPTS)


def test_build_version_texts_includes_beginner_rationale() -> None:
    versions = build_version_texts("core_task_scope.objective")
    assert [item.level for item in versions] == [
        ClarificationLevel.BEGINNER,
        ClarificationLevel.STANDARD,
        ClarificationLevel.ADVANCED,
    ]
    beginner = versions[0]
    assert beginner.rationale is not None
    assert "why" in beginner.rationale.lower() or "goal" in beginner.rationale.lower()
    assert versions[1].prompt == STANDARD_PROMPTS["core_task_scope.objective"]
    assert versions[2].prompt == ADVANCED_PROMPTS["core_task_scope.objective"]
    assert versions[1].rationale is None


def test_ranker_attaches_all_versions() -> None:
    question = ClarificationQuestionRanker().build_question(
        "technical_context.environment",
        question_number=1,
        total_questions=15,
    )
    assert len(question.versions) == 3
    assert question.versions[1].level is ClarificationLevel.STANDARD
    assert question.prompt == STANDARD_PROMPTS["technical_context.environment"]


def test_clarification_versions_available_defaults_and_fallback() -> None:
    defaults = ClarificationVersionsAvailable()
    assert defaults.enabled_levels() == ["beginner", "standard", "advanced"]
    none_enabled = ClarificationVersionsAvailable(
        beginner=False,
        standard=False,
        advanced=False,
    )
    assert none_enabled.enabled_levels() == ["standard"]


def test_beginner_option_guides_cover_every_quick_reply() -> None:
    assert_guides_cover_all_options()
    guides = build_quick_reply_guides("technical_context.environment")
    assert len(guides) == 5
    assert guides[0].option == "Python 3.12 with FastAPI and Pydantic v2"
    assert "stack" in guides[0].when_to_use.lower() or "project" in guides[0].when_to_use.lower()


def test_ask_the_locals_falls_back_without_model() -> None:
    result = AskTheLocalsService(llm=None).ask(
        initial_request="Write a FastAPI signup endpoint",
        card=RequirementCard(),
        field_name="technical_context.environment",
    )
    assert result.model_available is False
    assert result.insight == ""
    assert result.recommended_answer == ""
    assert result.message is not None
    assert "unavailable" in result.message.lower()


def test_ask_the_locals_uses_previous_answers_for_recommendation() -> None:
    captured: dict[str, object] = {}

    def responder(messages: list[ChatMessage]) -> str:
        captured["user"] = messages[-1].content
        return json.dumps(
            {
                "insight": "Stay consistent with the FastAPI stack already chosen.",
                "recommended_answer": "Use Pydantic v2 request models matching the existing signup schema.",
            }
        )

    card = RequirementCard(
        technical_context={"environment": "Python 3.12 with FastAPI"},
        core_task_scope={"objective": "Add a user signup endpoint"},
    )
    result = AskTheLocalsService(MockLLMClient(chat_responder=responder)).ask(
        initial_request="Write a FastAPI signup endpoint",
        card=card,
        field_name="inputs_outputs_contracts.inputs",
        last_answer="Python 3.12 with FastAPI",
        asked_fields=["technical_context.environment"],
        model_source="ai-tooling",
    )

    assert result.model_available is True
    assert result.recommended_answer.startswith("Use Pydantic")
    assert "technical_context.environment" in result.previous_answers_used
    assert "core_task_scope.objective" in result.previous_answers_used
    assert "inputs_outputs_contracts.inputs" not in result.previous_answers_used
    user_payload = json.loads(str(captured["user"]))
    assert user_payload["previous_answers"]["technical_context.environment"] == (
        "Python 3.12 with FastAPI"
    )
    assert "Contextual recommendation" in (result.message or "")


def test_collect_previous_answers_skips_empty_and_active_field() -> None:
    card = RequirementCard(
        technical_context={"environment": "Python 3.12"},
        core_task_scope={"objective": "Build signup"},
    )
    answers = collect_previous_answers(card, exclude_field="technical_context.environment")
    assert "technical_context.environment" not in answers
    assert answers["core_task_scope.objective"] == "Build signup"


def test_ask_the_locals_api_route(client: TestClient) -> None:
    create = client.post(
        "/sessions",
        json={"initial_request": "Write a FastAPI endpoint for user signup"},
    )
    assert create.status_code == 201
    session_id = create.json()["session"]["id"]
    response = client.post(f"/sessions/{session_id}/clarify/locals")
    assert response.status_code == 200
    payload = response.json()
    assert payload["field_name"]
    assert payload["model_available"] is False
    assert "unavailable" in (payload["message"] or "").lower()


def test_session_api_returns_clarification_versions(client: TestClient) -> None:
    create = client.post(
        "/sessions",
        json={"initial_request": "Write a FastAPI endpoint for user signup"},
    )
    assert create.status_code == 201
    payload = create.json()
    versions = payload["clarification_versions"]
    assert len(versions) == 3
    assert [item["level"] for item in versions] == ["beginner", "standard", "advanced"]
    assert versions[0]["rationale"]
    assert versions[1]["prompt"]


def test_user_settings_api_clarification_versions(client: TestClient) -> None:
    current = client.get("/settings/user")
    assert current.status_code == 200
    body = current.json()
    assert body["clarification_versions"] == {
        "beginner": True,
        "standard": True,
        "advanced": True,
    }
    assert body["ask_the_locals_api_override"]["configured"] is False
    update = {
        "llm_enabled": body["llm_enabled"],
        "precision_warning_threshold": body["precision_warning_threshold"],
        "similarity_time_scope_index": body["similarity_time_scope_index"],
        "clarification_versions": {
            "beginner": True,
            "standard": False,
            "advanced": True,
        },
        "default_api_endpoint_id": body["default_api_endpoint_id"],
        "api_endpoints": [
            {
                "id": endpoint["id"],
                "label": endpoint["label"],
                "base_url": endpoint["base_url"],
                "chat_model": endpoint["chat_model"],
            }
            for endpoint in body["api_endpoints"]
        ],
        "ai_tooling_api_override": {
            "label": body["ai_tooling_api_override"]["label"],
            "base_url": body["ai_tooling_api_override"]["base_url"],
            "chat_model": body["ai_tooling_api_override"]["chat_model"],
        },
        "ask_the_locals_api_override": {
            "label": "Locals",
            "base_url": "https://locals.example/v1",
            "chat_model": "locals-model",
        },
    }
    saved = client.put("/settings/user", json=update)
    assert saved.status_code == 200
    assert saved.json()["clarification_versions"] == {
        "beginner": True,
        "standard": False,
        "advanced": True,
    }
    assert saved.json()["ask_the_locals_override_active"] is True
    assert saved.json()["ask_the_locals_api_override"]["chat_model"] == "locals-model"
