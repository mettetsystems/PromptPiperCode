from pathlib import Path

from prompt_piper.setup.download_model import (
    download_configured_model,
    plan_model_download,
)


def test_plan_model_download_reads_env(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    models_dir = tmp_path / "models"
    env_path.write_text(
        "PROMPT_PIPER_LLM_ENABLED=true\n"
        "PROMPT_PIPER_LOCAL_MODEL_PRESET=qwen3-4b\n"
        "PROMPT_PIPER_LOCAL_MODEL_GGUF_REPO=Qwen/Qwen3-4B-GGUF\n"
        "PROMPT_PIPER_LOCAL_MODEL_GGUF_FILE=Qwen3-4B-Q4_K_M.gguf\n"
        "PROMPT_PIPER_LOCAL_MODEL_PATH=./data/models/Qwen3-4B-Q4_K_M.gguf\n",
        encoding="utf-8",
    )

    plan = plan_model_download(env_path=env_path, models_dir=models_dir)
    assert plan.cpu_only is False
    assert plan.repo == "Qwen/Qwen3-4B-GGUF"
    assert plan.filename == "Qwen3-4B-Q4_K_M.gguf"
    assert plan.local_dir == models_dir.resolve()


def test_download_configured_model_skips_cpu_only(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "PROMPT_PIPER_LLM_ENABLED=false\n"
        "PROMPT_PIPER_LOCAL_MODEL_PRESET=cpu-only\n",
        encoding="utf-8",
    )
    result = download_configured_model(env_path=env_path, models_dir=tmp_path / "models")
    assert result.status == "skipped"


def test_download_configured_model_reports_existing_file(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    gguf = models_dir / "Qwen3-4B-Q4_K_M.gguf"
    gguf.write_bytes(b"fake")
    env_path.write_text(
        "PROMPT_PIPER_LLM_ENABLED=true\n"
        "PROMPT_PIPER_LOCAL_MODEL_PRESET=qwen3-4b\n"
        "PROMPT_PIPER_LOCAL_MODEL_GGUF_REPO=Qwen/Qwen3-4B-GGUF\n"
        "PROMPT_PIPER_LOCAL_MODEL_GGUF_FILE=Qwen3-4B-Q4_K_M.gguf\n"
        f"PROMPT_PIPER_LOCAL_MODEL_PATH={gguf}\n",
        encoding="utf-8",
    )
    result = download_configured_model(env_path=env_path, models_dir=models_dir)
    assert result.status == "exists"
    assert result.path == gguf.resolve()
