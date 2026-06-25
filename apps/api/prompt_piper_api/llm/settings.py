from pydantic import BaseModel, Field

from prompt_piper_api.llm.enums import ModelProfile, ModelProvider


class ModelSettings(BaseModel):
    provider: ModelProvider
    base_url: str = Field(description="OpenAI-compatible API base URL, typically ending in /v1.")
    model_name: str
    api_key: str | None = None
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=1)
    enabled: bool = True
    profile: ModelProfile = ModelProfile.COMPATIBILITY


def profile_defaults(profile: ModelProfile) -> tuple[float, int]:
    if profile is ModelProfile.QUALITY:
        return 0.4, 2048
    return 0.2, 1024
