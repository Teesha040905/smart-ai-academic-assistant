"""Small in-memory rate limiter (sliding window).

Good for a single backend instance (Render free tier). Counters reset when the
process restarts, which is acceptable for brute-force and quota protection.
"""

from __future__ import annotations

import math
import threading
import time
from collections import defaultdict, deque
from typing import Callable, Deque

from fastapi import Depends, Request

from app.core.config import get_settings
from app.core.deps import get_current_user
from app.core.errors import AppError
from app.models.doc import Doc

_lock = threading.Lock()
_hits: dict[str, Deque[float]] = defaultdict(deque)


def reset() -> None:
    """Clear all counters (used by tests)."""
    with _lock:
        _hits.clear()


def client_ip(request: Request) -> str:
    # Render sits behind Cloudflare, which sets CF-Connecting-IP and overwrites any
    # client-supplied value, so it cannot be spoofed the way X-Forwarded-For can.
    cf = request.headers.get("cf-connecting-ip")
    if cf:
        return cf.strip()
    return request.client.host if request.client else "unknown"


def _check(key: str, limit: int, window_seconds: int, *, record: bool = True) -> None:
    if not get_settings().rate_limit_enabled:
        return
    now = time.monotonic()
    with _lock:
        q = _hits[key]
        while q and q[0] <= now - window_seconds:
            q.popleft()
        if len(q) >= limit:
            retry = max(1, math.ceil(q[0] + window_seconds - now))
            raise AppError(
                f"Too many requests. Please wait {_human(retry)} and try again.",
                status_code=429,
                code="rate_limited",
            )
        if record:
            q.append(now)


def hit(key: str, limit: int, window_seconds: int) -> None:
    """Count one event for ``key``; raise 429 if the limit is already reached."""
    _check(key, limit, window_seconds)


def ensure_allowed(key: str, limit: int, window_seconds: int) -> None:
    """Raise 429 if ``key`` is over the limit, without counting a new event."""
    _check(key, limit, window_seconds, record=False)


def clear(key: str) -> None:
    with _lock:
        _hits.pop(key, None)


def _human(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds} seconds"
    minutes = math.ceil(seconds / 60)
    return f"{minutes} minute{'s' if minutes != 1 else ''}"


def limit_by_ip(name: str, limit: int, window_seconds: int) -> Callable:
    """FastAPI dependency: ``limit`` requests per ``window_seconds`` per client IP."""

    def _dep(request: Request) -> None:
        hit(f"{name}:ip:{client_ip(request)}", limit, window_seconds)

    return _dep


def limit_ai_by_user(user: Doc = Depends(get_current_user)) -> Doc:
    """FastAPI dependency for AI endpoints: per-student minute and daily caps."""
    settings = get_settings()
    hit(f"ai:min:{user.id}", settings.ai_rate_limit_per_minute, 60)
    hit(f"ai:day:{user.id}", settings.ai_rate_limit_per_day, 24 * 3600)
    return user


# Login: failed attempts per account (not spoofable) — successful login clears it.
LOGIN_FAILS_PER_EMAIL = 5
LOGIN_FAIL_WINDOW = 15 * 60


def login_email_key(email: str) -> str:
    return f"login-fail:email:{email.strip().lower()}"


def check_login_allowed(email: str) -> None:
    ensure_allowed(login_email_key(email), LOGIN_FAILS_PER_EMAIL, LOGIN_FAIL_WINDOW)


def record_login_failure(email: str) -> None:
    # Only record; the *next* attempt is the one that gets blocked by check_login_allowed.
    with _lock:
        _hits[login_email_key(email)].append(time.monotonic())


def record_login_success(email: str) -> None:
    clear(login_email_key(email))
