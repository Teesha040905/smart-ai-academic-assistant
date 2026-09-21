import logging
import sys
from typing import Any

from app.core.config import get_settings


def setup_logging() -> None:
    settings = get_settings()
    level = logging.DEBUG if settings.debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        stream=sys.stdout,
    )
    # Quiet noisy libs
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_event(logger: logging.Logger, event: str, **fields: Any) -> None:
    """Structured-ish log line without secrets."""
    safe = {k: v for k, v in fields.items() if k.lower() not in {"password", "token", "api_key", "secret"}}
    parts = " ".join(f"{k}={v}" for k, v in safe.items())
    logger.info("%s %s", event, parts)
