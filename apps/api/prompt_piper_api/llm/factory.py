import os
from functools import lru_cache

from prompt_piper_api.config import Settings, get_settings
from prompt_piper_api.llm.base import LLMClient
from prompt_piper_api.llm.enums import ModelProvider
from prompt_piper_api.llm.local_openai import LocalOpenAICompatibleClient
from prompt_piper_api.llm.settings import ModelSettings, profile_defaults


class ExternalProviderDisabledError(RuntimeError):
    """Raised when external inference is requested but not explicitly enabled."""


def load_local_chat_settings(settings: Settings | None = None) -> ModelSettings:
    from prompt_piper_api.services.user_settings_service import get_user_settings_service

    app_settings = settings or get_settings()
    user_settings = get_user_settings_service()
    temperature, max_tokens = profile_defaults(app_settings.prompt_piper_model_profile)
    enabled = user_settings.is_llm_enabled(app_settings)
    override = user_settings.load().ai_tooling_api_override
    if override.configured:
        return ModelSettings(
            provider=ModelProvider.EXTERNAL_OPENAI_COMPATIBLE,
            base_url=override.base_url.strip(),
            model_name=override.chat_model.strip(),
            api_key=override.api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            enabled=enabled,
            profile=app_settings.prompt_piper_model_profile,
        )
    return ModelSettings(
        provider=ModelProvider.LOCAL_OPENAI_COMPATIBLE,
        base_url=app_settings.prompt_piper_local_base_url,
        model_name=app_settings.prompt_piper_local_chat_model,
        api_key=app_settings.prompt_piper_local_api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        enabled=enabled,
        profile=app_settings.prompt_piper_model_profile,
    )


def load_external_chat_settings(settings: Settings | None = None) -> ModelSettings:
    app_settings = settings or get_settings()
    if not app_settings.prompt_piper_external_enabled:
        raise ExternalProviderDisabledError(
            "External providers are disabled. Set PROMPT_PIPER_EXTERNAL_ENABLED=true to opt in."
        )
    temperature, max_tokens = profile_defaults(app_settings.prompt_piper_model_profile)
    return ModelSettings(
        provider=ModelProvider.EXTERNAL_OPENAI_COMPATIBLE,
        base_url=app_settings.prompt_piper_external_base_url,
        model_name=app_settings.prompt_piper_external_chat_model,
        api_key=app_settings.prompt_piper_external_api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        enabled=True,
        profile=app_settings.prompt_piper_model_profile,
    )


class ExternalOpenAICompatibleClient(LocalOpenAICompatibleClient):
    """OpenAI-compatible client for explicitly enabled external providers."""


def create_local_client(settings: Settings | None = None) -> LocalOpenAICompatibleClient:
    app_settings = settings or get_settings()
    chat_settings = load_local_chat_settings(app_settings)
    return LocalOpenAICompatibleClient(
        chat_settings,
        embed_model_name=app_settings.prompt_piper_local_embed_model,
    )


def create_external_client(settings: Settings | None = None) -> ExternalOpenAICompatibleClient:
    app_settings = settings or get_settings()
    chat_settings = load_external_chat_settings(app_settings)
    return ExternalOpenAICompatibleClient(
        chat_settings,
        embed_model_name=app_settings.prompt_piper_external_embed_model,
    )


def create_llm_client(
    settings: Settings | None = None,
    *,
    prefer_external: bool = False,
) -> LLMClient | None:
    """Build the active LLM client from environment configuration."""
    from prompt_piper_api.services.user_settings_service import get_user_settings_service

    app_settings = settings or get_settings()
    if not get_user_settings_service().is_llm_enabled():
        return None

    if prefer_external and app_settings.prompt_piper_external_enabled:
        return create_external_client(app_settings)

    return create_local_client(app_settings)


def create_llm_client_from_env() -> LLMClient | None:
    return create_llm_client()


def create_ask_the_locals_client(
    settings: Settings | None = None,
) -> tuple[LLMClient | None, str]:
    """Build the LLM client for Ask The Locals.

    Prefers a dedicated Ask The Locals API override when configured (live, no restart).
    Otherwise uses the current AI tooling model (setup wizard or tooling override).
    """
    from prompt_piper_api.services.user_settings_service import get_user_settings_service

    app_settings = settings or get_settings()
    user_settings = get_user_settings_service()
    if not user_settings.is_llm_enabled(app_settings):
        return None, "disabled"

    locals_override = user_settings.load().ask_the_locals_api_override
    if locals_override.configured:
        temperature, max_tokens = profile_defaults(app_settings.prompt_piper_model_profile)
        chat_settings = ModelSettings(
            provider=ModelProvider.EXTERNAL_OPENAI_COMPATIBLE,
            base_url=locals_override.base_url.strip(),
            model_name=locals_override.chat_model.strip(),
            api_key=locals_override.api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            enabled=True,
            profile=app_settings.prompt_piper_model_profile,
        )
        label = locals_override.label.strip() or locals_override.chat_model.strip()
        return (
            LocalOpenAICompatibleClient(
                chat_settings,
                embed_model_name=app_settings.prompt_piper_local_embed_model,
            ),
            f"Ask The Locals API ({label})",
        )

    client = create_llm_client(app_settings)
    if client is None:
        return None, "unavailable"
    tooling = user_settings.load().ai_tooling_api_override
    if tooling.configured:
        label = tooling.label.strip() or tooling.chat_model.strip()
        return client, f"Current AI tooling ({label})"
    return (
        client,
        f"Current AI tooling ({app_settings.prompt_piper_local_chat_model})",
    )


@lru_cache
def get_default_llm_client() -> LLMClient | None:
    return create_llm_client_from_env()


def clear_llm_client_cache() -> None:
    get_default_llm_client.cache_clear()


def env_snapshot() -> dict[str, str | None]:
    """Expose relevant model env vars for tests."""
    return {
        "PROMPT_PIPER_LOCAL_BASE_URL": os.getenv("PROMPT_PIPER_LOCAL_BASE_URL"),
        "PROMPT_PIPER_LOCAL_CHAT_MODEL": os.getenv("PROMPT_PIPER_LOCAL_CHAT_MODEL"),
        "PROMPT_PIPER_LOCAL_EMBED_MODEL": os.getenv("PROMPT_PIPER_LOCAL_EMBED_MODEL"),
        "PROMPT_PIPER_EXTERNAL_ENABLED": os.getenv("PROMPT_PIPER_EXTERNAL_ENABLED"),
    }
