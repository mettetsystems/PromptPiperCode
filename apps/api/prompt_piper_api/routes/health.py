from fastapi import APIRouter

from prompt_piper_api import __version__
from prompt_piper_api.config import get_settings
from prompt_piper_api.llm.factory import create_llm_client_from_env, load_local_chat_settings
from prompt_piper_api.schemas.health import HealthResponse, LlmHealthResponse, utc_now
from prompt_piper_api.services.user_settings_service import get_user_settings_service

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    settings = get_settings()
    database = "sqlite" if settings.is_sqlite else "postgresql"
    return HealthResponse(
        status="ok",
        service="prompt-piper-api",
        version=__version__,
        timestamp=utc_now(),
        database=database,
    )


@router.get("/health/llm", response_model=LlmHealthResponse)
def llm_health_check() -> LlmHealthResponse:
    settings = get_settings()
    user_settings = get_user_settings_service()
    if not user_settings.is_llm_enabled():
        chat_settings = load_local_chat_settings(settings)
        return LlmHealthResponse(
            llm_enabled=False,
            status="disabled",
            endpoint=chat_settings.base_url,
            model_name=chat_settings.model_name,
            message="Local LLM disabled (CPU-only / rule-based mode).",
            checked_at=utc_now(),
        )

    chat_settings = load_local_chat_settings(settings)
    client = create_llm_client_from_env()
    if client is None:
        return LlmHealthResponse(
            llm_enabled=False,
            status="disabled",
            endpoint=chat_settings.base_url,
            model_name=chat_settings.model_name,
            message="LLM client not configured.",
            checked_at=utc_now(),
        )

    probe = client.health_check()
    return LlmHealthResponse(
        llm_enabled=True,
        status="ok" if probe.ok else "unreachable",
        endpoint=chat_settings.base_url,
        model_name=probe.model_name or chat_settings.model_name,
        message=probe.message,
        checked_at=utc_now(),
    )
