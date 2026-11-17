"""Collection helpers for MongoDB CRUD."""

from __future__ import annotations

from typing import Any, Optional

from pymongo.database import Database

from app.models.doc import Doc, from_mongo, touch


RELATION_KEYS = {
    "profile",
    "units",
    "topics",
    "messages",
    "sessions",
    "questions",
    "answers",
    "chunks",
    "attempts",
}


def insert(db: Database, collection: str, doc: Doc) -> Doc:
    touch(doc)
    payload = _payload(doc)
    db[collection].insert_one(payload)
    return doc


def save(db: Database, collection: str, doc: Doc) -> Doc:
    touch(doc)
    payload = _payload(doc)
    db[collection].replace_one({"id": doc.id}, payload, upsert=True)
    return doc


def _payload(doc: Doc) -> dict[str, Any]:
    # Temporarily drop in-memory relations so they are not persisted
    stashed = {}
    for key in list(doc.__dict__.keys()):
        if key in RELATION_KEYS:
            stashed[key] = getattr(doc, key)
            delattr(doc, key)
    try:
        return doc.to_mongo()
    finally:
        for key, value in stashed.items():
            setattr(doc, key, value)

def find_one(db: Database, collection: str, query: dict[str, Any]) -> Optional[Doc]:
    return from_mongo(db[collection].find_one(query))


def find_many(
    db: Database,
    collection: str,
    query: dict[str, Any],
    *,
    sort: Optional[list[tuple[str, int]]] = None,
    limit: Optional[int] = None,
) -> list[Doc]:
    cursor = db[collection].find(query)
    if sort:
        cursor = cursor.sort(sort)
    if limit is not None:
        cursor = cursor.limit(limit)
    return [d for d in (from_mongo(x) for x in cursor) if d is not None]


def delete_one(db: Database, collection: str, query: dict[str, Any]) -> int:
    return db[collection].delete_one(query).deleted_count


def delete_many(db: Database, collection: str, query: dict[str, Any]) -> int:
    return db[collection].delete_many(query).deleted_count


def count(db: Database, collection: str, query: dict[str, Any]) -> int:
    return db[collection].count_documents(query)
