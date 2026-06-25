from __future__ import annotations

from pathlib import Path


def venv_pip_command(repo_root: Path | None = None) -> str:
    root = repo_root or Path(__file__).resolve().parents[4]
    return str(root / "apps" / "api" / ".venv" / "bin" / "pip")


def venv_hf_command(repo_root: Path | None = None) -> str:
    root = repo_root or Path(__file__).resolve().parents[4]
    return str(root / "apps" / "api" / ".venv" / "bin" / "hf")


def hf_download_command(
    repo: str,
    filename: str,
    *,
    local_dir: str = "data/models",
) -> str:
    return f"hf download {repo} {filename} --local-dir {local_dir}"


def hf_cli_install_lines(*, repo_root: Path | None = None) -> tuple[str, ...]:
    """Shell commands and notes for installing the Hugging Face `hf` CLI."""
    pip = venv_pip_command(repo_root)
    hf = venv_hf_command(repo_root)
    return (
        "Install Hugging Face CLI (once, for GGUF downloads):",
        f'  {pip} install "huggingface_hub[cli]"',
        f"  # then use: {hf} download ...",
        "  hf auth login   # optional; required for some gated models",
    )


def hf_cli_env_comments(*, repo_root: Path | None = None) -> tuple[str, ...]:
    """Comment lines written into .env when an SLM preset needs a model download."""
    pip = venv_pip_command(repo_root)
    return (
        "# GGUF download tooling (hf CLI; huggingface-cli is deprecated):",
        f'#   {pip} install "huggingface_hub[cli]"',
        "#   hf auth login  # optional; gated models only",
    )


# Backward-compatible aliases for older imports.
huggingface_cli_install_lines = hf_cli_install_lines
huggingface_cli_env_comments = hf_cli_env_comments
