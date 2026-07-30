from __future__ import annotations

from pydantic import BaseModel, Field

SIMILARITY_TIME_SCOPE_LABELS: tuple[str, ...] = (
    "1 hour or less",
    "24 hours",
    "7 days",
    "30 days",
    "1 year",
    "1 year or greater",
)

SIMILARITY_TIME_SCOPE_HOURS: tuple[float | None, ...] = (
    1.0,
    24.0,
    168.0,
    720.0,
    8760.0,
    None,
)

MAX_API_ENDPOINT_SLOTS = 6


class ClarificationVersionsAvailable(BaseModel):
    """Which clarification wording levels appear in the UI. All on by default."""

    beginner: bool = True
    standard: bool = True
    advanced: bool = True

    def enabled_levels(self) -> list[str]:
        levels: list[str] = []
        if self.beginner:
            levels.append("beginner")
        if self.standard:
            levels.append("standard")
        if self.advanced:
            levels.append("advanced")
        if not levels:
            # Always keep at least standard so clarification remains usable.
            levels.append("standard")
        return levels


class ApiEndpointConfig(BaseModel):
    id: str
    label: str = ""
    base_url: str = ""
    chat_model: str = ""
    api_key: str | None = None

    @property
    def configured(self) -> bool:
        return bool(self.base_url.strip() and self.chat_model.strip())


class AiToolingApiOverride(BaseModel):
    """Optional external API that replaces the setup wizard local model after API restart."""

    label: str = ""
    base_url: str = ""
    chat_model: str = ""
    api_key: str | None = None

    @property
    def configured(self) -> bool:
        return bool(self.base_url.strip() and self.chat_model.strip())


class AskTheLocalsApiOverride(BaseModel):
    """Optional API used only by Ask The Locals (live; no API restart required)."""

    label: str = ""
    base_url: str = ""
    chat_model: str = ""
    api_key: str | None = None

    @property
    def configured(self) -> bool:
        return bool(self.base_url.strip() and self.chat_model.strip())


class UserSettings(BaseModel):
    llm_enabled: bool = True
    precision_warning_threshold: float = Field(default=0.75, ge=0.0, le=1.0)
    similarity_time_scope_index: int = Field(default=5, ge=0, le=5)
    clarification_versions: ClarificationVersionsAvailable = Field(
        default_factory=ClarificationVersionsAvailable,
    )
    default_api_endpoint_id: str | None = None
    api_endpoints: list[ApiEndpointConfig] = Field(default_factory=list)
    ai_tooling_api_override: AiToolingApiOverride = Field(default_factory=AiToolingApiOverride)
    ask_the_locals_api_override: AskTheLocalsApiOverride = Field(
        default_factory=AskTheLocalsApiOverride,
    )

    def normalized_endpoints(self) -> list[ApiEndpointConfig]:
        return self.api_endpoints[:MAX_API_ENDPOINT_SLOTS]

    def endpoint_by_id(self, endpoint_id: str | None) -> ApiEndpointConfig | None:
        if not endpoint_id:
            return None
        for endpoint in self.normalized_endpoints():
            if endpoint.id == endpoint_id:
                return endpoint
        return None

    def similarity_scope_hours(self) -> float | None:
        return SIMILARITY_TIME_SCOPE_HOURS[self.similarity_time_scope_index]
