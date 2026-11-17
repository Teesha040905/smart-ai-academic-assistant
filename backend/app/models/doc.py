"""MongoDB document helpers — attribute-access objects compatible with Pydantic from_attributes."""

from __future__ import annotations

from datetime import date, datetime, time, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


def new_uuid() -> str:
    return str(uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Doc:
    """Mutable document with attribute access."""

    def __init__(self, **kwargs: Any):
        for key, value in kwargs.items():
            object.__setattr__(self, key, value)

    def __repr__(self) -> str:
        ident = getattr(self, "id", None)
        return f"<Doc id={ident!r}>"

    def to_mongo(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for key, value in self.__dict__.items():
            if key.startswith("_"):
                continue
            data[key] = _serialize(value)
        # Keep Mongo _id aligned with business id
        if "id" in data:
            data["_id"] = data["id"]
        return data

    def apply(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)


def _serialize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Doc):
        return value.to_mongo()
    if isinstance(value, list):
        return [_serialize(v) for v in value]
    if isinstance(value, datetime):
        return value
    if isinstance(value, date) and not isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, time):
        return value.isoformat()
    return value


def _deserialize_value(key: str, value: Any) -> Any:
    if value is None:
        return None
    # date-only fields stored as ISO strings
    date_fields = {
        "exam_date",
        "start_date",
        "end_date",
        "scheduled_date",
        "activity_date",
    }
    time_fields = {"start_time", "end_time", "exam_time"}
    if key in date_fields and isinstance(value, str):
        return date.fromisoformat(value)
    if key in time_fields and isinstance(value, str):
        return time.fromisoformat(value)
    return value


def from_mongo(data: Optional[dict[str, Any]]) -> Optional[Doc]:
    if not data:
        return None
    payload = dict(data)
    payload.pop("_id", None)
    if "id" not in payload and data.get("_id") is not None:
        payload["id"] = str(data["_id"])
    cleaned = {k: _deserialize_value(k, v) for k, v in payload.items()}
    # Restore enums where applicable
    for enum_key, enum_cls in _ENUM_FIELDS.items():
        if enum_key in cleaned and cleaned[enum_key] is not None and not isinstance(cleaned[enum_key], enum_cls):
            try:
                cleaned[enum_key] = enum_cls(cleaned[enum_key])
            except (ValueError, KeyError):
                pass
    return Doc(**cleaned)


def touch(doc: Doc) -> None:
    doc.updated_at = utcnow()


# Late-bound enum map filled after enums import in models package
_ENUM_FIELDS: dict[str, type[Enum]] = {}


def register_enum_fields(mapping: dict[str, type[Enum]]) -> None:
    _ENUM_FIELDS.update(mapping)
