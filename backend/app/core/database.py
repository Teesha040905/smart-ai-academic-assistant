from collections.abc import Generator
from functools import lru_cache

from pymongo import ASCENDING, MongoClient
from pymongo.database import Database

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_client: MongoClient | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        settings = get_settings()
        _client = MongoClient(settings.mongodb_url, serverSelectionTimeoutMS=5000)
    return _client


def get_database() -> Database:
    settings = get_settings()
    return get_client()[settings.mongodb_db]


def get_db() -> Generator[Database, None, None]:
    yield get_database()


def close_client() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None


def ensure_indexes(db: Database | None = None) -> None:
    if db is None:
        db = get_database()
    db.users.create_index("email", unique=True)
    db.users.create_index("id", unique=True)
    db.student_profiles.create_index("user_id", unique=True)
    db.subjects.create_index([("user_id", ASCENDING), ("name", ASCENDING)])
    db.subjects.create_index("id", unique=True)
    db.units.create_index([("user_id", ASCENDING), ("subject_id", ASCENDING)])
    db.topics.create_index([("user_id", ASCENDING), ("subject_id", ASCENDING)])
    db.documents.create_index([("user_id", ASCENDING), ("created_at", ASCENDING)])
    db.document_chunks.create_index([("document_id", ASCENDING), ("chunk_index", ASCENDING)])
    db.conversations.create_index([("user_id", ASCENDING), ("updated_at", ASCENDING)])
    db.messages.create_index([("conversation_id", ASCENDING), ("created_at", ASCENDING)])
    db.study_plans.create_index([("user_id", ASCENDING), ("is_active", ASCENDING)])
    db.study_sessions.create_index([("user_id", ASCENDING), ("scheduled_date", ASCENDING)])
    db.quizzes.create_index([("user_id", ASCENDING), ("created_at", ASCENDING)])
    db.quiz_attempts.create_index([("user_id", ASCENDING), ("quiz_id", ASCENDING)])
    db.flashcards.create_index([("user_id", ASCENDING), ("next_review_at", ASCENDING)])
    db.exams.create_index([("user_id", ASCENDING), ("exam_date", ASCENDING)])
    db.assignments.create_index([("user_id", ASCENDING), ("deadline", ASCENDING)])
    db.recommendations.create_index([("user_id", ASCENDING), ("score", ASCENDING)])
    db.study_activities.create_index([("user_id", ASCENDING), ("activity_date", ASCENDING)])
    db.password_reset_tokens.create_index("token_hash", unique=True)
    logger.info("mongodb_indexes_ready db=%s", db.name)


@lru_cache
def ping_mongo() -> bool:
    get_client().admin.command("ping")
    return True
