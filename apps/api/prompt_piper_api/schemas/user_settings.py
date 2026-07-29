from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from prompt_piper_api.config import Settings
from prompt_piper_api.domain.user_settings import (
    SIMILARITY_TIME_SCOPE_LABELS,
    MAX_API_ENDPOINT_SLOTS,
    AiToolingApiOverride,
    ApiEndpointConfig,
    ClarificationVersionsAvailable,
    UserSettings,
)


class ApiEndpointResponse(BaseModel):
    id: str
    label: str
    base_url: str
    chat_model: str
    api_key_configured: bool
    configured: bool


class SetupAiToolingResponse(BaseModel):
    base_url: str
    chat_model: str
    source: str = "Setup wizard (.env)"


class AiToolingApiOverrideResponse(BaseModel):
    label: str
    base_url: str
    chat_model: str
    api_key_configured: bool
    configured: bool


class AiToolingApiOverrideUpdate(BaseModel):
    label: str = ""
    base_url: str = ""
    chat_model: str = ""
    api_key: str | None = None


class ClarificationVersionsSettings(BaseModel):
    beginner: bool = True
    standard: bool = True
    advanced: bool = True


class UserSettingsResponse(BaseModel):
    llm_enabled: bool
    precision_warning_threshold: float = Field(ge=0.0, le=1.0)
    similarity_time_scope_index: int = Field(ge=0, le=5)
    similarity_time_scope_label: str
    similarity_time_scope_labels: list[str]
    clarification_versions: ClarificationVersionsSettings
    default_api_endpoint_id: str | None
    api_endpoints: list[ApiEndpointResponse]
    max_api_endpoint_slots: int = MAX_API_ENDPOINT_SLOTS
    setup_ai_tooling: SetupAiToolingResponse
    ai_tooling_api_override: AiToolingApiOverrideResponse
    ai_tooling_override_active: bool


class ApiEndpointUpdate(BaseModel):
    id: str = ""
    label: str = ""
    base_url: str = ""
    chat_model: str = ""
    api_key: str | None = None


class UserSettingsUpdateRequest(BaseModel):
    llm_enabled: bool
    precision_warning_threshold: float = Field(ge=0.0, le=1.0)
    similarity_time_scope_index: int = Field(ge=0, le=5)
    clarification_versions: ClarificationVersionsSettings = Field(
        default_factory=ClarificationVersionsSettings,
    )
    default_api_endpoint_id: str | None = None
    api_endpoints: list[ApiEndpointUpdate] = Field(default_factory=list)
    ai_tooling_api_override: AiToolingApiOverrideUpdate = Field(
        default_factory=AiToolingApiOverrideUpdate,
    )


def _padded_endpoints(settings: UserSettings) -> list[ApiEndpointConfig]:
    endpoints = list(settings.normalized_endpoints())
    while len(endpoints) < MAX_API_ENDPOINT_SLOTS:
        endpoints.append(ApiEndpointConfig(id=str(uuid.uuid4())))
    return endpoints[:MAX_API_ENDPOINT_SLOTS]


def to_user_settings_response(
    settings: UserSettings,
    app_settings: Settings,
) -> UserSettingsResponse:
    endpoints = _padded_endpoints(settings)
    override = settings.ai_tooling_api_override
    versions = settings.clarification_versions
    return UserSettingsResponse(
        llm_enabled=settings.llm_enabled,
        precision_warning_threshold=settings.precision_warning_threshold,
        similarity_time_scope_index=settings.similarity_time_scope_index,
        similarity_time_scope_label=SIMILARITY_TIME_SCOPE_LABELS[settings.similarity_time_scope_index],
        similarity_time_scope_labels=list(SIMILARITY_TIME_SCOPE_LABELS),
        clarification_versions=ClarificationVersionsSettings(
            beginner=versions.beginner,
            standard=versions.standard,
            advanced=versions.advanced,
        ),
        default_api_endpoint_id=settings.default_api_endpoint_id,
        api_endpoints=[
            ApiEndpointResponse(
                id=endpoint.id,
                label=endpoint.label,
                base_url=endpoint.base_url,
                chat_model=endpoint.chat_model,
                api_key_configured=bool(endpoint.api_key),
                configured=endpoint.configured,
            )
            for endpoint in endpoints
        ],
        setup_ai_tooling=SetupAiToolingResponse(
            base_url=app_settings.prompt_piper_local_base_url,
            chat_model=app_settings.prompt_piper_local_chat_model,
        ),
        ai_tooling_api_override=AiToolingApiOverrideResponse(
            label=override.label,
            base_url=override.base_url,
            chat_model=override.chat_model,
            api_key_configured=bool(override.api_key),
            configured=override.configured,
        ),
        ai_tooling_override_active=override.configured,
    )


def to_user_settings(update: UserSettingsUpdateRequest) -> UserSettings:
    return UserSettings(
        llm_enabled=update.llm_enabled,
        precision_warning_threshold=update.precision_warning_threshold,
        similarity_time_scope_index=update.similarity_time_scope_index,
        clarification_versions=ClarificationVersionsAvailable(
            beginner=update.clarification_versions.beginner,
            standard=update.clarification_versions.standard,
            advanced=update.clarification_versions.advanced,
        ),
        default_api_endpoint_id=update.default_api_endpoint_id,
        api_endpoints=[
            ApiEndpointConfig(
                id=item.id,
                label=item.label,
                base_url=item.base_url,
                chat_model=item.chat_model,
                api_key=item.api_key,
            )
            for item in update.api_endpoints
        ],
        ai_tooling_api_override=AiToolingApiOverride(
            label=update.ai_tooling_api_override.label,
            base_url=update.ai_tooling_api_override.base_url,
            chat_model=update.ai_tooling_api_override.chat_model,
            api_key=update.ai_tooling_api_override.api_key,
        ),
    )
