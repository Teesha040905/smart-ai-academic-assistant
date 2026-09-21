"""OpenAI-compatible LLM client with graceful degradation."""

from __future__ import annotations

import json
from typing import Any, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.logging import get_logger

logger = get_logger(__name__)


class AIClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def enabled(self) -> bool:
        return bool(self.settings.ai_api_key)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.ai_api_key}",
            "Content-Type": "application/json",
        }

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4), reraise=True)
    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.4,
        response_format: Optional[dict[str, Any]] = None,
    ) -> str:
        if not self.enabled:
            raise AppError(
                "AI is not configured. Set AI_API_KEY in your environment.",
                status_code=503,
                code="ai_unavailable",
            )
        payload: dict[str, Any] = {
            "model": self.settings.ai_chat_model,
            "messages": messages,
            "temperature": temperature,
        }
        if response_format:
            payload["response_format"] = response_format
        try:
            with httpx.Client(timeout=90.0) as client:
                resp = client.post(
                    f"{self.settings.ai_base_url.rstrip('/')}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except httpx.HTTPError as exc:
            logger.exception("ai_chat_failed")
            raise AppError(
                "We couldn't reach the AI service right now. Your study data is safe — try again later.",
                status_code=503,
                code="ai_unavailable",
            ) from exc

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not self.enabled:
            # Deterministic local fallback embeddings for offline/dev without API key
            return [self._hash_embed(t) for t in texts]
        payload = {"model": self.settings.ai_embedding_model, "input": texts}
        try:
            with httpx.Client(timeout=90.0) as client:
                resp = client.post(
                    f"{self.settings.ai_base_url.rstrip('/')}/embeddings",
                    headers=self._headers(),
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                return [item["embedding"] for item in data["data"]]
        except httpx.HTTPError as exc:
            logger.warning("embed_api_failed falling_back_local error=%s", str(exc))
            return [self._hash_embed(t) for t in texts]

    def _hash_embed(self, text: str) -> list[float]:
        """Lightweight bag-of-words style vector for local RAG demos without an API key."""
        dim = self.settings.embedding_dimensions
        vec = [0.0] * dim
        tokens = text.lower().split()
        if not tokens:
            return vec
        for tok in tokens:
            h = hash(tok) % dim
            vec[h] += 1.0
        # L2 normalize
        norm = sum(v * v for v in vec) ** 0.5 or 1.0
        return [v / norm for v in vec]

    def chat_json(self, messages: list[dict[str, str]], temperature: float = 0.3) -> Any:
        raw = self.chat(
            messages,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Try to extract JSON object
            start = raw.find("{")
            end = raw.rfind("}")
            if start >= 0 and end > start:
                return json.loads(raw[start : end + 1])
            raise AppError("AI returned invalid JSON", status_code=502, code="ai_bad_response")
