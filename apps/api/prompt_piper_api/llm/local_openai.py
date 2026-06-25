from typing import Any

import httpx

from prompt_piper_api.llm.base import (
    ChatMessage,
    ChatResponse,
    EmbedResponse,
    HealthCheckResult,
    LLMError,
)
from prompt_piper_api.llm.enums import ModelProvider
from prompt_piper_api.llm.settings import ModelSettings


class LocalOpenAICompatibleClient:
    """OpenAI-compatible client for local servers such as llama.cpp."""

    def __init__(
        self,
        settings: ModelSettings,
        *,
        embed_model_name: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._settings = settings
        self._embed_model_name = embed_model_name or settings.model_name
        self._timeout = timeout
        self._base_url = settings.base_url.rstrip("/")

    @property
    def provider(self) -> ModelProvider:
        return self._settings.provider

    @property
    def settings(self) -> ModelSettings:
        return self._settings

    @property
    def embed_model_name(self) -> str:
        return self._embed_model_name

    def chat(
        self,
        messages: list[ChatMessage],
        *,
        response_format: dict[str, Any] | None = None,
    ) -> ChatResponse:
        payload: dict[str, Any] = {
            "model": self._settings.model_name,
            "messages": [message.model_dump() for message in messages],
            "temperature": self._settings.temperature,
            "max_tokens": self._settings.max_tokens,
        }
        if response_format is not None:
            payload["response_format"] = response_format

        data = self._post("/chat/completions", payload)
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError("Unexpected chat completion response shape") from exc

        return ChatResponse(
            content=content,
            model=data.get("model", self._settings.model_name),
            provider=self.provider,
        )

    def embed(self, texts: list[str]) -> EmbedResponse:
        if not texts:
            return EmbedResponse(vectors=[], model=self._embed_model_name, provider=self.provider)

        payload = {"model": self._embed_model_name, "input": texts}
        data = self._post("/embeddings", payload)
        try:
            vectors = [item["embedding"] for item in data["data"]]
        except (KeyError, TypeError) as exc:
            raise LLMError("Unexpected embeddings response shape") from exc

        return EmbedResponse(
            vectors=vectors,
            model=data.get("model", self._embed_model_name),
            provider=self.provider,
        )

    def health_check(self) -> HealthCheckResult:
        headers = self._headers()
        try:
            with httpx.Client(timeout=3.0) as client:
                response = client.get(f"{self._base_url}/models", headers=headers)
            if response.status_code == 200:
                return HealthCheckResult(
                    ok=True,
                    provider=self.provider,
                    message="Local OpenAI-compatible endpoint is reachable.",
                    model_name=self._settings.model_name,
                )
            return HealthCheckResult(
                ok=False,
                provider=self.provider,
                message=f"Local endpoint returned HTTP {response.status_code}.",
                model_name=self._settings.model_name,
            )
        except httpx.HTTPError as exc:
            return HealthCheckResult(
                ok=False,
                provider=self.provider,
                message=f"Local endpoint unreachable: {exc}",
                model_name=self._settings.model_name,
            )

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        headers = self._headers()
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(
                    f"{self._base_url}{path}",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMError(str(exc)) from exc

        data = response.json()
        if not isinstance(data, dict):
            raise LLMError("Expected JSON object response from LLM endpoint")
        return data

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._settings.api_key:
            headers["Authorization"] = f"Bearer {self._settings.api_key}"
        return headers
