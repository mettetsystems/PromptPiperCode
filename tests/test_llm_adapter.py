import json
from unittest.mock import patch

import httpx
import pytest
from prompt_piper_api.config import Settings
from prompt_piper_api.domain.requirement_card import RequirementCard
from prompt_piper_api.llm.base import ChatMessage
from prompt_piper_api.llm.enums import ModelProfile, ModelProvider
from prompt_piper_api.llm.factory import (
    ExternalProviderDisabledError,
    create_external_client,
    create_llm_client,
    create_local_client,
    load_external_chat_settings,
    load_local_chat_settings,
)
from prompt_piper_api.llm.local_openai import LocalOpenAICompatibleClient
from prompt_piper_api.llm.mock import MockLLMClient
from prompt_piper_api.llm.settings import ModelSettings
from prompt_piper_api.services.draft_generator import DraftGenerator
from prompt_piper_api.services.requirement_card_extractor import RequirementCardExtractor


def test_external_provider_not_used_unless_explicitly_enabled() -> None:
    settings = Settings(
        prompt_piper_external_enabled=False,
        prompt_piper_external_base_url="https://api.openai.com/v1",
        prompt_piper_external_api_key="secret-key",
    )

    with pytest.raises(ExternalProviderDisabledError):
        load_external_chat_settings(settings)

    with pytest.raises(ExternalProviderDisabledError):
        create_external_client(settings)

    client = create_llm_client(settings, prefer_external=True)
    assert isinstance(client, LocalOpenAICompatibleClient)
    assert client.provider is ModelProvider.LOCAL_OPENAI_COMPATIBLE


def test_external_provider_available_when_enabled() -> None:
    settings = Settings(
        prompt_piper_external_enabled=True,
        prompt_piper_external_base_url="https://api.openai.com/v1",
        prompt_piper_external_chat_model="gpt-4o-mini",
        prompt_piper_external_api_key="secret-key",
    )

    external_settings = load_external_chat_settings(settings)
    assert external_settings.provider is ModelProvider.EXTERNAL_OPENAI_COMPATIBLE
    assert external_settings.enabled is True

    client = create_llm_client(settings, prefer_external=True)
    assert client is not None
    assert client.provider is ModelProvider.EXTERNAL_OPENAI_COMPATIBLE


def test_mock_client_chat_embed_and_health() -> None:
    mock = MockLLMClient()

    chat = mock.chat([ChatMessage(role="user", content="hello")])
    embed = mock.embed(["alpha", "beta"])
    health = mock.health_check()

    assert chat.content.startswith("mock-response:")
    assert chat.provider is ModelProvider.LOCAL_OPENAI_COMPATIBLE
    assert len(embed.vectors) == 2
    assert health.ok is True
    assert len(mock.chat_calls) == 1
    assert mock.embed_calls == [["alpha", "beta"]]


def test_local_client_config_loads_from_settings() -> None:
    settings = Settings(
        prompt_piper_local_base_url="http://127.0.0.1:9090/v1",
        prompt_piper_local_chat_model="local-chat",
        prompt_piper_local_embed_model="local-embed",
        prompt_piper_model_profile=ModelProfile.QUALITY,
    )

    chat_settings = load_local_chat_settings(settings)
    client = create_local_client(settings)

    assert chat_settings.base_url == "http://127.0.0.1:9090/v1"
    assert chat_settings.model_name == "local-chat"
    assert chat_settings.provider is ModelProvider.LOCAL_OPENAI_COMPATIBLE
    assert chat_settings.profile is ModelProfile.QUALITY
    assert chat_settings.temperature == 0.4
    assert chat_settings.max_tokens == 2048
    assert client.embed_model_name == "local-embed"


def test_fallback_when_local_model_is_not_running() -> None:
    settings = ModelSettings(
        provider=ModelProvider.LOCAL_OPENAI_COMPATIBLE,
        base_url="http://127.0.0.1:1/v1",
        model_name="offline-model",
        enabled=True,
    )
    client = LocalOpenAICompatibleClient(settings)

    health = client.health_check()
    assert health.ok is False

    extractor = RequirementCardExtractor(client)
    card = extractor.extract("Write a release note prompt for engineers")

    assert card.objective == "Write a release note prompt for engineers"

    generator = DraftGenerator(client)
    draft = generator.generate(RequirementCard(objective="Summarize incidents"))

    assert "Mission" in draft.body
    assert "unspecified" in draft.body.lower()


def test_services_use_mock_llm_when_healthy() -> None:
    card_json = json.dumps({"objective": "LLM parsed objective", "audience": "Developers"})

    mock = MockLLMClient(
        chat_responder=lambda _messages: card_json,
    )
    extractor = RequirementCardExtractor(mock)
    card = extractor.extract("ignored by mock")

    assert card.objective == "LLM parsed objective"
    assert card.audience == "Developers"


def test_local_client_health_check_success() -> None:
    settings = ModelSettings(
        provider=ModelProvider.LOCAL_OPENAI_COMPATIBLE,
        base_url="http://mock.local/v1",
        model_name="llama",
    )
    client = LocalOpenAICompatibleClient(settings)

    mock_response = httpx.Response(status_code=200, json={"data": []})
    with patch("httpx.Client.get", return_value=mock_response):
        health = client.health_check()

    assert health.ok is True
    assert health.model_name == "llama"
