from __future__ import annotations

from pathlib import Path

from prompt_piper_api.config import Settings
from prompt_piper_api.domain.user_settings import (
    AiToolingApiOverride,
    ApiEndpointConfig,
    UserSettings,
)
from prompt_piper_api.llm.factory import load_local_chat_settings
from prompt_piper_api.services.user_settings_service import UserSettingsService


def test_user_settings_round_trip(tmp_path: Path) -> None:
    service = UserSettingsService(tmp_path / "user_settings.json")
    saved = service.save(
        UserSettings(
            llm_enabled=False,
            precision_warning_threshold=0.8,
            similarity_time_scope_index=2,
            api_endpoints=[
                ApiEndpointConfig(
                    id="slot-1",
                    label="OpenAI",
                    base_url="https://api.openai.com/v1",
                    chat_model="gpt-4o-mini",
                    api_key="sk-test",
                )
            ],
            default_api_endpoint_id="slot-1",
            ai_tooling_api_override=AiToolingApiOverride(
                label="Remote SLM",
                base_url="https://example.com/v1",
                chat_model="qwen",
                api_key="tooling-key",
            ),
        ),
    )
    loaded = service.load()
    assert loaded.llm_enabled is False
    assert loaded.precision_warning_threshold == 0.8
    assert loaded.default_api_endpoint_id == "slot-1"
    assert loaded.endpoint_by_id("slot-1") is not None
    assert saved.api_endpoints[0].api_key == "sk-test"
    assert loaded.ai_tooling_api_override.chat_model == "qwen"
    assert loaded.ai_tooling_api_override.api_key == "tooling-key"


def test_user_settings_preserves_api_key_when_blank_in_update(tmp_path: Path) -> None:
    path = tmp_path / "user_settings.json"
    service = UserSettingsService(path)
    service.save(
        UserSettings(
            api_endpoints=[
                ApiEndpointConfig(
                    id="slot-1",
                    label="OpenAI",
                    base_url="https://api.openai.com/v1",
                    chat_model="gpt-4o-mini",
                    api_key="sk-secret",
                )
            ],
            ai_tooling_api_override=AiToolingApiOverride(
                label="Tooling",
                base_url="https://example.com/v1",
                chat_model="qwen",
                api_key="tooling-secret",
            ),
        ),
    )
    service.update(
        UserSettings(
            llm_enabled=True,
            precision_warning_threshold=0.75,
            similarity_time_scope_index=5,
            default_api_endpoint_id=None,
            api_endpoints=[
                ApiEndpointConfig(
                    id="slot-1",
                    label="OpenAI",
                    base_url="https://api.openai.com/v1",
                    chat_model="gpt-4o-mini",
                    api_key=None,
                )
            ],
            ai_tooling_api_override=AiToolingApiOverride(
                label="Tooling",
                base_url="https://example.com/v1",
                chat_model="qwen",
                api_key=None,
            ),
        ),
    )
    loaded = service.load()
    assert loaded.api_endpoints[0].api_key == "sk-secret"
    assert loaded.ai_tooling_api_override.api_key == "tooling-secret"


def test_load_local_chat_settings_uses_ai_tooling_override(tmp_path: Path, monkeypatch) -> None:
    settings_path = tmp_path / "user_settings.json"
    service = UserSettingsService(settings_path)
    service.save(
        UserSettings(
            ai_tooling_api_override=AiToolingApiOverride(
                label="Remote",
                base_url="https://override.example/v1",
                chat_model="override-model",
                api_key="override-key",
            ),
        ),
    )

    app_settings = Settings(
        registry_path=tmp_path / "registry",
        artifacts_path=tmp_path / "artifacts",
        audit_log_path=tmp_path / "audit",
        prompt_piper_export_root=tmp_path,
        prompt_piper_host_export_root=tmp_path,
        prompt_piper_registry_root=tmp_path / "registry",
        prompt_piper_artifact_root=tmp_path / "artifacts",
        prompt_piper_local_base_url="http://127.0.0.1:8080/v1",
        prompt_piper_local_chat_model="local-model",
    )

    monkeypatch.setattr(
        "prompt_piper_api.services.user_settings_service.get_user_settings_service",
        lambda: service,
    )

    chat_settings = load_local_chat_settings(app_settings)
    assert chat_settings.base_url == "https://override.example/v1"
    assert chat_settings.model_name == "override-model"
    assert chat_settings.api_key == "override-key"
