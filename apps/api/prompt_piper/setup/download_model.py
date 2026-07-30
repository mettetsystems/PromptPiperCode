"""Download the GGUF configured in .env into data/models/."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from prompt_piper.setup.llama_launcher import find_llama_server
from prompt_piper.setup.paths import repo_root


@dataclass(frozen=True)
class ModelDownloadPlan:
    repo: str
    filename: str
    local_dir: Path
    target_path: Path
    preset: str | None
    cpu_only: bool
    requires_auth_hint: bool


@dataclass(frozen=True)
class ModelDownloadResult:
    status: str
    message: str
    path: Path | None = None


def _load_env(env_path: Path) -> dict[str, str]:
    if not env_path.is_file():
        return {}
    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def plan_model_download(
    *,
    env_path: Path | None = None,
    models_dir: Path | None = None,
) -> ModelDownloadPlan:
    root = repo_root()
    target_env = env_path or (root / ".env")
    env = _load_env(target_env)
    local_dir = models_dir or (root / "data" / "models")
    preset = env.get("PROMPT_PIPER_LOCAL_MODEL_PRESET")
    cpu_only = preset == "cpu-only" or env.get("PROMPT_PIPER_LLM_ENABLED", "true").lower() in {
        "0",
        "false",
        "no",
        "off",
    }
    repo = env.get("PROMPT_PIPER_LOCAL_MODEL_GGUF_REPO", "").strip()
    filename = env.get("PROMPT_PIPER_LOCAL_MODEL_GGUF_FILE", "").strip()
    configured_path = env.get("PROMPT_PIPER_LOCAL_MODEL_PATH", "").strip()
    if configured_path:
        target_path = Path(configured_path)
        if not target_path.is_absolute():
            target_path = (root / target_path).resolve()
    elif filename:
        target_path = (local_dir / filename).resolve()
    else:
        target_path = local_dir.resolve()
    requires_auth = "google/" in repo or "gemma" in (preset or "").lower()
    return ModelDownloadPlan(
        repo=repo,
        filename=filename,
        local_dir=local_dir.resolve(),
        target_path=target_path,
        preset=preset,
        cpu_only=cpu_only,
        requires_auth_hint=requires_auth,
    )


def download_configured_model(
    *,
    env_path: Path | None = None,
    models_dir: Path | None = None,
    force: bool = False,
) -> ModelDownloadResult:
    """Download the GGUF named in .env. Skips when the file already exists."""
    plan = plan_model_download(env_path=env_path, models_dir=models_dir)
    if plan.cpu_only:
        return ModelDownloadResult(
            status="skipped",
            message="CPU-only mode is configured; no GGUF download is required.",
        )
    if not plan.repo or not plan.filename:
        return ModelDownloadResult(
            status="error",
            message=(
                "No GGUF repo/file in .env. Run make setup and choose a Gemma/Qwen preset, "
                "or set PROMPT_PIPER_LOCAL_MODEL_GGUF_REPO and PROMPT_PIPER_LOCAL_MODEL_GGUF_FILE."
            ),
        )
    if plan.target_path.is_file() and not force:
        return ModelDownloadResult(
            status="exists",
            message=f"Model already present: {plan.target_path}",
            path=plan.target_path,
        )

    plan.local_dir.mkdir(parents=True, exist_ok=True)
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        return ModelDownloadResult(
            status="error",
            message=(
                "huggingface_hub is not installed. Run: make setup-model-deps\n"
                "Then retry: make download-model"
            ),
        )

    try:
        downloaded = hf_hub_download(
            repo_id=plan.repo,
            filename=plan.filename,
            local_dir=str(plan.local_dir),
        )
    except Exception as exc:  # noqa: BLE001 - surface HF auth/network errors to the user
        hint = ""
        if plan.requires_auth_hint:
            hint = " If this is a gated Gemma repo, run: hf auth login"
        return ModelDownloadResult(
            status="error",
            message=f"Download failed for {plan.repo}/{plan.filename}: {exc}.{hint}",
        )

    path = Path(downloaded).resolve()
    return ModelDownloadResult(
        status="downloaded",
        message=f"Downloaded {plan.filename} → {path}",
        path=path,
    )


def llama_server_status_message() -> str:
    binary = find_llama_server()
    if binary is not None:
        return f"llama-server found: {binary}"
    return (
        "llama-server not found on PATH. Install llama.cpp and ensure `llama-server` is "
        "executable (or set LLAMA_SERVER=/path/to/llama-server). "
        "See docs/local-setup.md."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Download the GGUF model configured in .env into data/models/.",
    )
    parser.add_argument("--env-file", type=Path, default=None)
    parser.add_argument("--models-dir", type=Path, default=None)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if the GGUF file already exists.",
    )
    parser.add_argument(
        "--check-llama",
        action="store_true",
        help="Also print whether llama-server is available.",
    )
    args = parser.parse_args(argv)

    result = download_configured_model(
        env_path=args.env_file,
        models_dir=args.models_dir,
        force=args.force,
    )
    print(result.message)
    if args.check_llama:
        print(llama_server_status_message())
    if result.status == "error":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
