from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from prompt_piper.setup.ensure_llm import EnsureLlmResult, ensure_local_llm, shell_export
from prompt_piper.setup.gpu_detect import GpuInfo
from prompt_piper.setup.llama_launcher import resolve_model_path


def test_resolve_model_path_prefers_existing_gguf(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    models = tmp_path / "data" / "models"
    models.mkdir(parents=True)
    model = models / "google_gemma-3-1b-it-Q4_K_M.gguf"
    model.write_bytes(b"gguf")

    monkeypatch.setattr("prompt_piper.setup.llama_launcher.repo_root", lambda: tmp_path)

    resolved = resolve_model_path(
        configured_path="./data/models/missing.gguf",
        preset_id="gemma3-1b",
    )
    assert resolved == model.resolve()


def test_ensure_local_llm_cpu_only_without_gpu(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "PROMPT_PIPER_LLM_ENABLED=true\n"
        "PROMPT_PIPER_LOCAL_MODEL_PRESET=gemma3-1b\n"
        "PROMPT_PIPER_LOCAL_BASE_URL=http://127.0.0.1:8080/v1\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("prompt_piper.setup.ensure_llm.repo_root", lambda: tmp_path)
    monkeypatch.setattr("prompt_piper.setup.ensure_llm.detect_gpu", lambda: None)
    monkeypatch.setattr("prompt_piper.setup.ensure_llm.is_server_healthy", lambda *_args, **_kwargs: False)

    result = ensure_local_llm(env_path)
    assert result.mode == "cpu_only"
    assert result.llm_enabled is False
    assert "No compatible GPU" in result.message


def test_ensure_local_llm_skips_cpu_only_preset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("PROMPT_PIPER_LOCAL_MODEL_PRESET=cpu-only\n", encoding="utf-8")
    monkeypatch.setattr("prompt_piper.setup.ensure_llm.repo_root", lambda: tmp_path)

    result = ensure_local_llm(env_path)
    assert result.mode == "skipped"
    assert result.llm_enabled is False


def test_ensure_local_llm_uses_running_server(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "PROMPT_PIPER_LLM_ENABLED=true\n"
        "PROMPT_PIPER_LOCAL_MODEL_PRESET=gemma3-1b\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("prompt_piper.setup.ensure_llm.repo_root", lambda: tmp_path)
    monkeypatch.setattr("prompt_piper.setup.ensure_llm.is_server_healthy", lambda *_args, **_kwargs: True)

    result = ensure_local_llm(env_path)
    assert result.mode == "already_running"
    assert result.llm_enabled is True


def test_shell_export() -> None:
    enabled = shell_export(EnsureLlmResult(mode="gpu", llm_enabled=True, message="ok"))
    disabled = shell_export(EnsureLlmResult(mode="cpu_only", llm_enabled=False, message="ok"))
    assert enabled == "export PROMPT_PIPER_LLM_ENABLED=true"
    assert disabled == "export PROMPT_PIPER_LLM_ENABLED=false"


def test_detect_gpu_returns_none_without_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    from prompt_piper.setup.gpu_detect import detect_gpu

    monkeypatch.setattr("prompt_piper.setup.gpu_detect.shutil.which", lambda _name: None)
    monkeypatch.setattr("prompt_piper.setup.gpu_detect._amd_devices_present", lambda: False)
    assert detect_gpu() is None


def test_detect_gpu_nvidia(monkeypatch: pytest.MonkeyPatch) -> None:
    from prompt_piper.setup.gpu_detect import detect_gpu

    monkeypatch.setattr(
        "prompt_piper.setup.gpu_detect.shutil.which",
        lambda name: "/usr/bin/nvidia-smi" if name == "nvidia-smi" else None,
    )

    class Completed:
        stdout = "NVIDIA GeForce RTX 4090, 24564\n"

        returncode = 0

    monkeypatch.setattr("prompt_piper.setup.gpu_detect.subprocess.run", lambda *args, **kwargs: Completed())
    gpu = detect_gpu()
    assert gpu is not None
    assert gpu.vendor == "nvidia"
    assert gpu.vram_mb == 24564
