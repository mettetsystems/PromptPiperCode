from collections.abc import Callable
from typing import TypeVar

from prompt_piper_api.llm.base import LLMClient

T = TypeVar("T")


def with_llm_fallback[T](
    llm: LLMClient | None,
    llm_fn: Callable[[LLMClient], T],
    fallback_fn: Callable[[], T],
) -> T:
    """Try an LLM-backed path when the client is healthy; otherwise use fallback."""
    if llm is None:
        return fallback_fn()
    try:
        health = llm.health_check()
        if not health.ok:
            return fallback_fn()
        return llm_fn(llm)
    except Exception:
        return fallback_fn()
