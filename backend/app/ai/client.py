"""OpenAI-compatible LLM client with multi-key failover and graceful degradation."""

from __future__ import annotations

import json
import threading
import zlib
from typing import Any, Optional

import httpx

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.logging import get_logger

logger = get_logger(__name__)


class AIClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._keys: list[str] = list(self.settings.ai_api_key_list)
        self._current_idx: int = 0
        self._lock = threading.Lock()

    @property
    def enabled(self) -> bool:
        return bool(self._keys)

    def _get_current_key(self) -> str:
        with self._lock:
            if not self._keys:
                return ""
            return self._keys[self._current_idx % len(self._keys)]

    def _rotate_key(self, failed_key: str, reason: str = "") -> str:
        with self._lock:
            if not self._keys:
                return ""
            curr = self._keys[self._current_idx % len(self._keys)]
            if curr == failed_key or len(self._keys) > 1:
                self._current_idx = (self._current_idx + 1) % len(self._keys)
            new_key = self._keys[self._current_idx % len(self._keys)]
            logger.warning(
                "ai_key_rotated reason=%s old_tail=%s new_tail=%s active_index=%d/%d",
                reason,
                failed_key[-6:] if failed_key else "none",
                new_key[-6:] if new_key else "none",
                (self._current_idx % len(self._keys)) + 1,
                len(self._keys),
            )
            return new_key

    def _headers_for(self, key: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

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

        attempts = max(1, len(self._keys))
        last_error: Exception | None = None

        for attempt in range(attempts):
            active_key = self._get_current_key()
            try:
                with httpx.Client(timeout=30.0) as client:
                    resp = client.post(
                        f"{self.settings.ai_base_url.rstrip('/')}/chat/completions",
                        headers=self._headers_for(active_key),
                        json=payload,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as exc:
                last_error = exc
                status = exc.response.status_code
                reason = f"http_{status}"
                logger.warning(
                    "ai_chat_attempt_failed attempt=%d/%d status=%d key_tail=%s error=%s",
                    attempt + 1,
                    attempts,
                    status,
                    active_key[-6:] if active_key else "",
                    str(exc),
                )
                if len(self._keys) > 1 and attempt < attempts - 1:
                    self._rotate_key(active_key, reason=reason)
                    continue
                break
            except (httpx.TimeoutException, httpx.RequestError) as exc:
                last_error = exc
                reason = "network_timeout_or_error"
                logger.warning(
                    "ai_chat_attempt_failed attempt=%d/%d key_tail=%s error=%s",
                    attempt + 1,
                    attempts,
                    active_key[-6:] if active_key else "",
                    str(exc),
                )
                if len(self._keys) > 1 and attempt < attempts - 1:
                    self._rotate_key(active_key, reason=reason)
                    continue
                break

        logger.warning("ai_chat_all_keys_failed error=%s", str(last_error))
        # Callers (tutor, quiz, flashcards, summarize) each have a subject-aware fallback for this
        raise AppError(
            "AI is temporarily unavailable. Please try again later.",
            status_code=503,
            code="ai_unavailable",
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not self.enabled:
            return [self._hash_embed(t) for t in texts]

        payload = {"model": self.settings.ai_embedding_model, "input": texts}
        attempts = max(1, len(self._keys))

        for attempt in range(attempts):
            active_key = self._get_current_key()
            try:
                with httpx.Client(timeout=30.0) as client:
                    resp = client.post(
                        f"{self.settings.ai_base_url.rstrip('/')}/embeddings",
                        headers=self._headers_for(active_key),
                        json=payload,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    return [item["embedding"] for item in data["data"]]
            except (httpx.HTTPStatusError, httpx.TimeoutException, httpx.RequestError) as exc:
                logger.warning(
                    "embed_attempt_failed attempt=%d/%d key_tail=%s error=%s",
                    attempt + 1,
                    attempts,
                    active_key[-6:] if active_key else "",
                    str(exc),
                )
                if len(self._keys) > 1 and attempt < attempts - 1:
                    self._rotate_key(active_key, reason="embed_error")
                    continue
                break

        logger.warning("embed_api_failed falling_back_local")
        return [self._hash_embed(t) for t in texts]

    def _hash_embed(self, text: str) -> list[float]:
        dim = self.settings.embedding_dimensions
        vec = [0.0] * dim
        tokens = text.lower().split()
        if not tokens:
            return vec
        for tok in tokens:
            # crc32 is stable across processes; built-in hash() is salted per interpreter run
            h = zlib.crc32(tok.encode("utf-8")) % dim
            vec[h] += 1.0
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
            start = raw.find("{")
            end = raw.rfind("}")
            if start >= 0 and end > start:
                return json.loads(raw[start : end + 1])
            raise AppError("AI returned invalid JSON", status_code=502, code="ai_bad_response")
