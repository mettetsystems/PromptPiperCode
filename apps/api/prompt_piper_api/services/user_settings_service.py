from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from pathlib import Path

from prompt_piper_api.config import Settings, get_settings
from prompt_piper_api.domain.user_settings import (
    MAX_API_ENDPOINT_SLOTS,
    AiToolingApiOverride,
    ApiEndpointConfig,
    AskTheLocalsApiOverride,
    UserSettings,
)


class UserSettingsService:
    """Persisted user preferences (runtime-updatable without API restart)."""

    def __init__(self, path: Path | None = None) -> None:
        settings = get_settings()
        self._path = path or settings.user_settings_path

    def load(self) -> UserSettings:
        if not self._path.is_file():
            return UserSettings()
        payload = json.loads(self._path.read_text(encoding="utf-8"))
        data = UserSettings.model_validate(payload)
        return data.model_copy(update={"api_endpoints": data.normalized_endpoints()})

    def save(self, settings: UserSettings) -> UserSettings:
        normalized = settings.model_copy(
            update={"api_endpoints": settings.normalized_endpoints()[:MAX_API_ENDPOINT_SLOTS]},
        )
        if (
            normalized.default_api_endpoint_id is not None
            and normalized.endpoint_by_id(normalized.default_api_endpoint_id) is None
        ):
            normalized = normalized.model_copy(update={"default_api_endpoint_id": None})
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(normalized.model_dump(), indent=2, ensure_ascii=True),
            encoding="utf-8",
        )
        return normalized

    def update(self, patch: UserSettings) -> UserSettings:
        current = self.load()
        merged_endpoints = self._merge_endpoints(current.api_endpoints, patch.api_endpoints)
        merged_override = self._merge_ai_tooling_override(
            current.ai_tooling_api_override,
            patch.ai_tooling_api_override,
        )
        merged_locals = self._merge_ask_the_locals_override(
            current.ask_the_locals_api_override,
            patch.ask_the_locals_api_override,
        )
        merged = current.model_copy(
            update={
                "llm_enabled": patch.llm_enabled,
                "precision_warning_threshold": patch.precision_warning_threshold,
                "similarity_time_scope_index": patch.similarity_time_scope_index,
                "clarification_versions": patch.clarification_versions,
                "default_api_endpoint_id": patch.default_api_endpoint_id,
                "api_endpoints": merged_endpoints,
                "ai_tooling_api_override": merged_override,
                "ask_the_locals_api_override": merged_locals,
            },
        )
        return self.save(merged)

    def is_llm_enabled(self, app_settings: Settings | None = None) -> bool:
        settings = app_settings or get_settings()
        if not settings.prompt_piper_llm_enabled:
            return False
        return self.load().llm_enabled

    def precision_warning_threshold(self) -> float:
        return self.load().precision_warning_threshold

    def similarity_min_indexed_at(self) -> datetime | None:
        hours = self.load().similarity_scope_hours()
        if hours is None:
            return None
        return datetime.now(tz=UTC) - timedelta(hours=hours)

    def ai_tooling_override_configured(self) -> bool:
        return self.load().ai_tooling_api_override.configured

    @staticmethod
    def _merge_ai_tooling_override(
        existing: AiToolingApiOverride,
        incoming: AiToolingApiOverride,
    ) -> AiToolingApiOverride:
        api_key = incoming.api_key
        if not api_key and existing.configured:
            api_key = existing.api_key
        return incoming.model_copy(update={"api_key": api_key})

    @staticmethod
    def _merge_ask_the_locals_override(
        existing: AskTheLocalsApiOverride,
        incoming: AskTheLocalsApiOverride,
    ) -> AskTheLocalsApiOverride:
        api_key = incoming.api_key
        if not api_key and existing.configured:
            api_key = existing.api_key
        return incoming.model_copy(update={"api_key": api_key})

    @staticmethod
    def _merge_endpoints(
        existing: list[ApiEndpointConfig],
        incoming: list[ApiEndpointConfig],
    ) -> list[ApiEndpointConfig]:
        existing_by_id = {endpoint.id: endpoint for endpoint in existing}
        merged: list[ApiEndpointConfig] = []
        for index in range(MAX_API_ENDPOINT_SLOTS):
            if index < len(incoming):
                endpoint = incoming[index]
                endpoint_id = endpoint.id.strip() or str(uuid.uuid4())
                prior = existing_by_id.get(endpoint_id)
                api_key = endpoint.api_key
                if not api_key and prior is not None:
                    api_key = prior.api_key
                merged.append(
                    endpoint.model_copy(
                        update={
                            "id": endpoint_id,
                            "api_key": api_key,
                        },
                    ),
                )
            elif index < len(existing):
                merged.append(existing[index])
            else:
                merged.append(ApiEndpointConfig(id=str(uuid.uuid4())))
        return merged[:MAX_API_ENDPOINT_SLOTS]


@lru_cache(maxsize=1)
def get_user_settings_service() -> UserSettingsService:
    return UserSettingsService()


def clear_user_settings_cache() -> None:
    cache_clear = getattr(get_user_settings_service, "cache_clear", None)
    if cache_clear is not None:
        cache_clear()
