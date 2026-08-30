from __future__ import annotations

import os
import shutil
import signal
import subprocess
import time
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from prompt_piper.setup.gpu_detect import GpuInfo


@dataclass(frozen=True)
class LlamaServerConfig:
    host: str
    port: int
    context_size: int
    gpu_layers: int
    model_path: Path
    binary: Path


def repo_root() -> Path:
    override = os.getenv("PROMPT_PIPER_REPO_ROOT")
    if override and override.strip():
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parents[4]


def pid_file_path() -> Path:
    return repo_root() / "data" / ".llama-server.pid"


def find_llama_server() -> Path | None:
    override = os.getenv("LLAMA_SERVER")
    if override:
        path = Path(override).expanduser()
        if path.is_file() and os.access(path, os.X_OK):
            return path
    discovered = shutil.which("llama-server") or shutil.which("llama-server-bin")
    if discovered:
        return Path(discovered)
    for candidate in (
        Path("/usr/bin/llama-server"),
        Path("/usr/local/bin/llama-server"),
        Path.home() / ".local" / "bin" / "llama-server",
    ):
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


def resolve_model_path(
    *,
    configured_path: str | None,
    preset_id: str | None,
) -> Path | None:
    root = repo_root()
    if configured_path:
        path = Path(configured_path).expanduser()
        if not path.is_absolute():
            path = root / path
        if path.is_file():
            return path.resolve()

    models_dir = root / "data" / "models"
    if not models_dir.is_dir():
        return None

    if preset_id and preset_id not in {"cpu-only", "custom"}:
        from prompt_piper.setup.catalog import ALL_PRESETS, resolve_preset_id

        preset = ALL_PRESETS.get(resolve_preset_id(preset_id))
        if preset is not None:
            candidate = models_dir / preset.suggested_gguf_filename
            if candidate.is_file():
                return candidate.resolve()

    gguf_files = sorted(
        models_dir.glob("*.gguf"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    if gguf_files:
        return gguf_files[0].resolve()
    return None


def server_base_url(host: str, port: int) -> str:
    return f"http://{host}:{port}/v1"


def is_server_healthy(base_url: str, *, timeout: float = 3.0) -> bool:
    try:
        with urlopen(f"{base_url.rstrip('/')}/models", timeout=timeout) as response:
            return response.status == 200
    except (URLError, OSError, ValueError):
        return False


def build_server_config(
    *,
    model_path: Path,
    binary: Path,
    gpu: GpuInfo,
    host: str = "127.0.0.1",
    port: int = 8080,
    context_size: int = 4096,
) -> LlamaServerConfig:
    gpu_layers = int(os.getenv("PROMPT_PIPER_LLAMA_GPU_LAYERS", "999"))
    return LlamaServerConfig(
        host=host,
        port=port,
        context_size=context_size,
        gpu_layers=gpu_layers,
        model_path=model_path,
        binary=binary,
    )


def llama_command(config: LlamaServerConfig) -> list[str]:
    return [
        str(config.binary),
        "-m",
        str(config.model_path),
        "--host",
        config.host,
        "--port",
        str(config.port),
        "-c",
        str(config.context_size),
        "-ngl",
        str(config.gpu_layers),
    ]


def read_managed_pid() -> int | None:
    path = pid_file_path()
    if not path.is_file():
        return None
    try:
        pid = int(path.read_text(encoding="utf-8").strip())
    except ValueError:
        return None
    if pid <= 0:
        return None
    return pid


def _pid_is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _send_signal(pid: int, sig: int) -> None:
    try:
        os.killpg(pid, sig)
        return
    except ProcessLookupError:
        return
    except OSError:
        pass
    try:
        os.kill(pid, sig)
    except OSError:
        return


def stop_managed_server() -> bool:
    pid = read_managed_pid()
    if pid is None:
        return False
    if _pid_is_running(pid):
        _send_signal(pid, signal.SIGTERM)
        for _ in range(40):
            if not _pid_is_running(pid):
                break
            time.sleep(0.25)
        if _pid_is_running(pid):
            _send_signal(pid, signal.SIGKILL)
            time.sleep(0.25)
    with suppress(OSError):
        pid_file_path().unlink(missing_ok=True)
    return True


def start_server(
    config: LlamaServerConfig,
    *,
    log_path: Path | None = None,
) -> subprocess.Popen[str]:
    pid_file_path().parent.mkdir(parents=True, exist_ok=True)
    stdout = subprocess.DEVNULL
    stderr = subprocess.DEVNULL
    log_handle = None
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_handle = log_path.open("a", encoding="utf-8")
        stdout = log_handle
        stderr = log_handle

    process = subprocess.Popen(
        llama_command(config),
        stdout=stdout,
        stderr=stderr,
        start_new_session=True,
        text=True,
    )
    if log_handle is not None:
        log_handle.close()
    pid_file_path().write_text(str(process.pid), encoding="utf-8")
    return process


def wait_for_server(
    base_url: str,
    *,
    process: subprocess.Popen[str] | None = None,
    timeout_seconds: float = 120.0,
    poll_interval: float = 1.0,
) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if process is not None and process.poll() is not None:
            return False
        if is_server_healthy(base_url):
            return True
        time.sleep(poll_interval)
    return False
