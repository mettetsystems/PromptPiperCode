from datetime import datetime

from prompt_piper_api.config import Settings
from pydantic import BaseModel, Field


class SendToInferenceRequest(BaseModel):
    explicit_approval: bool = Field(
        default=False,
        description="Must be true to confirm sending the optimized prompt off-machine.",
    )
    api_endpoint_id: str | None = Field(
        default=None,
        description="Optional one-time API endpoint slot id. Uses dashboard default when omitted.",
    )


class SendToInferenceResponse(BaseModel):
    provider: str
    model: str
    prompt_id: str
    version: int = Field(ge=1)
    timestamp: datetime
    artifact_location: str
    inference_response_artifact_path: str
    response_text: str = ""


class InferenceEndpointOption(BaseModel):
    id: str
    label: str
    base_url: str
    chat_model: str
    configured: bool
    is_default: bool


class InferenceSettingsResponse(BaseModel):
    local_model_endpoint: str
    local_chat_model: str
    local_embed_model: str
    embedding_model: str
    external_inference_enabled: bool
    external_provider_base_url: str
    external_provider_model: str
    external_provider_api_key_configured: bool
    require_approval_before_external_call: bool
    send_to_inference_available: bool = False
    uses_local_model: bool = False
    llm_enabled: bool = True
    api_endpoints: list[InferenceEndpointOption] = Field(default_factory=list)
    default_api_endpoint_id: str | None = None


def to_inference_settings(
    settings: Settings,
    *,
    user_settings=None,
) -> InferenceSettingsResponse:
    from prompt_piper_api.services.user_settings_service import UserSettingsService

    prefs = (
        user_settings.load()
        if isinstance(user_settings, UserSettingsService)
        else UserSettingsService().load()
    )
    external = settings.external_inference_enabled
    local_env = settings.prompt_piper_llm_enabled
    llm_enabled = local_env and prefs.llm_enabled
    configured_slots = [endpoint for endpoint in prefs.normalized_endpoints() if endpoint.configured]
    endpoint_available = bool(configured_slots)
    return InferenceSettingsResponse(
        local_model_endpoint=settings.prompt_piper_local_base_url,
        local_chat_model=settings.prompt_piper_local_chat_model,
        local_embed_model=settings.prompt_piper_local_embed_model,
        embedding_model=settings.prompt_piper_embedding_model,
        external_inference_enabled=external,
        external_provider_base_url=settings.prompt_piper_external_base_url,
        external_provider_model=settings.prompt_piper_external_chat_model,
        external_provider_api_key_configured=bool(settings.prompt_piper_external_api_key),
        require_approval_before_external_call=settings.require_approval_before_external_call,
        send_to_inference_available=endpoint_available or external or llm_enabled,
        uses_local_model=llm_enabled and not external and not endpoint_available,
        llm_enabled=llm_enabled,
        default_api_endpoint_id=prefs.default_api_endpoint_id,
        api_endpoints=[
            InferenceEndpointOption(
                id=endpoint.id,
                label=endpoint.label or endpoint.chat_model or endpoint.base_url,
                base_url=endpoint.base_url,
                chat_model=endpoint.chat_model,
                configured=endpoint.configured,
                is_default=endpoint.id == prefs.default_api_endpoint_id,
            )
            for endpoint in configured_slots
        ],
    )
