"""Domain enums and MongoDB document factories."""

from __future__ import annotations

import enum
from datetime import date, datetime, time
from typing import Any, Optional

from app.models.doc import Doc, from_mongo, new_uuid, register_enum_fields, touch, utcnow


class UserRole(str, enum.Enum):
    student = "student"
    faculty = "faculty"
    admin = "admin"


class Difficulty(str, enum.Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class TopicStatus(str, enum.Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"


class DocumentStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    ready = "ready"
    failed = "failed"


class AssignmentStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    overdue = "overdue"


class QuestionType(str, enum.Enum):
    mcq = "mcq"
    true_false = "true_false"
    short_answer = "short_answer"
    conceptual = "conceptual"


class SessionStatus(str, enum.Enum):
    planned = "planned"
    completed = "completed"
    missed = "missed"
    cancelled = "cancelled"


class Priority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


register_enum_fields(
    {
        "role": UserRole,
        "difficulty": Difficulty,
        "priority": Priority,
        "question_type": QuestionType,
    }
)


def _base(**extra: Any) -> dict[str, Any]:
    now = utcnow()
    uid = new_uuid()
    data = {"id": uid, "created_at": now, "updated_at": now}
    data.update(extra)
    return data


def make_user(**kwargs: Any) -> Doc:
    defaults = _base(
        email="",
        hashed_password="",
        full_name="",
        role=UserRole.student,
        is_active=True,
        theme="system",
    )
    defaults.update(kwargs)
    if isinstance(defaults.get("role"), str):
        defaults["role"] = UserRole(defaults["role"])
    return Doc(**defaults)


def make_profile(**kwargs: Any) -> Doc:
    defaults = _base(
        user_id="",
        photo_url=None,
        course=None,
        branch=None,
        semester=None,
        academic_year=None,
        preferred_study_time=None,
        daily_study_hours=3.0,
        learning_preferences=None,
        academic_goals=None,
        notification_prefs=None,
        ai_prefs=None,
    )
    defaults.update(kwargs)
    return Doc(**defaults)


def make_subject(**kwargs: Any) -> Doc:
    defaults = _base(
        user_id="",
        name="",
        code=None,
        description=None,
        color="#2563eb",
        priority=Priority.medium,
        exam_date=None,
    )
    defaults.update(kwargs)
    if isinstance(defaults.get("priority"), str):
        defaults["priority"] = Priority(defaults["priority"])
    return Doc(**defaults)


def make_unit(**kwargs: Any) -> Doc:
    defaults = _base(
        subject_id="",
        user_id="",
        name="",
        order_index=0,
        progress_override=None,
    )
    defaults.update(kwargs)
    return Doc(**defaults)


def make_topic(**kwargs: Any) -> Doc:
    defaults = _base(
        user_id="",
        subject_id="",
        unit_id=None,
        name="",
        description=None,
        difficulty=Difficulty.medium,
        status=TopicStatus.not_started,
        knowledge_level=0.0,
        last_studied_at=None,
        revision_count=0,
        quiz_average=None,
        importance=1.0,
    )
    defaults.update(kwargs)
    if isinstance(defaults.get("difficulty"), str):
        defaults["difficulty"] = Difficulty(defaults["difficulty"])
    if isinstance(defaults.get("status"), str):
        defaults["status"] = TopicStatus(defaults["status"])
    return Doc(**defaults)


def make_document(**kwargs: Any) -> Doc:
    defaults = _base(
        user_id="",
        subject_id=None,
        unit_id=None,
        topic_id=None,
        title="",
        original_filename="",
        stored_filename="",
        mime_type="",
        file_size=0,
        status=DocumentStatus.pending,
        progress=0,
        error_message=None,
        page_count=None,
    )
    defaults.update(kwargs)
    if isinstance(defaults.get("status"), str):
        defaults["status"] = DocumentStatus(defaults["status"])
    return Doc(**defaults)


def make_chunk(**kwargs: Any) -> Doc:
    defaults = _base(
        document_id="",
        user_id="",
        chunk_index=0,
        page_number=None,
        content="",
        vector_id=None,
        token_estimate=0,
    )
    defaults.update(kwargs)
    return Doc(**defaults)


def make_conversation(**kwargs: Any) -> Doc:
    defaults = _base(user_id="", title="New conversation", subject_id=None)
    defaults.update(kwargs)
    return Doc(**defaults)


def make_message(**kwargs: Any) -> Doc:
    defaults = _base(
        conversation_id="",
        user_id="",
        role="user",
        content="",
        sources_json=None,
        used_rag=False,
        from_general_knowledge=False,
    )
    defaults.update(kwargs)
    return Doc(**defaults)


def make_study_plan(**kwargs: Any) -> Doc:
    defaults = _base(
        user_id="",
        title="Adaptive Study Plan",
        start_date=date.today(),
        end_date=date.today(),
        notes=None,
        is_active=True,
    )
    defaults.update(kwargs)
    return Doc(**defaults)


def make_study_session(**kwargs: Any) -> Doc:
    defaults = _base(
        user_id="",
        plan_id=None,
        subject_id=None,
        topic_id=None,
        title="",
        scheduled_date=date.today(),
        start_time=None,
        end_time=None,
        duration_minutes=30,
        status=SessionStatus.planned,
        activity_type="study",
        notes=None,
    )
    defaults.update(kwargs)
    if isinstance(defaults.get("status"), str):
        defaults["status"] = SessionStatus(defaults["status"])
    return Doc(**defaults)


def make_quiz(**kwargs: Any) -> Doc:
    defaults = _base(
        user_id="",
        subject_id=None,
        unit_id=None,
        topic_id=None,
        title="",
        difficulty=Difficulty.medium,
        question_count=10,
    )
    defaults.update(kwargs)
    if isinstance(defaults.get("difficulty"), str):
        defaults["difficulty"] = Difficulty(defaults["difficulty"])
    return Doc(**defaults)


def make_quiz_question(**kwargs: Any) -> Doc:
    defaults = _base(
        quiz_id="",
        question_type=QuestionType.mcq,
        prompt="",
        options_json=None,
        correct_answer="",
        explanation=None,
        topic_tag=None,
        order_index=0,
    )
    defaults.update(kwargs)
    if isinstance(defaults.get("question_type"), str):
        defaults["question_type"] = QuestionType(defaults["question_type"])
    return Doc(**defaults)


def make_quiz_attempt(**kwargs: Any) -> Doc:
    defaults = _base(
        quiz_id="",
        user_id="",
        score=0.0,
        max_score=0.0,
        percentage=0.0,
        strong_topics_json=None,
        weak_topics_json=None,
        completed_at=None,
    )
    defaults.update(kwargs)
    return Doc(**defaults)


def make_quiz_answer(**kwargs: Any) -> Doc:
    defaults = _base(
        attempt_id="",
        question_id="",
        user_answer="",
        is_correct=False,
    )
    defaults.update(kwargs)
    return Doc(**defaults)


def make_flashcard(**kwargs: Any) -> Doc:
    defaults = _base(
        user_id="",
        subject_id=None,
        topic_id=None,
        question="",
        answer="",
        difficulty=Difficulty.medium,
        review_status="new",
        ease_factor=2.5,
        interval_days=0,
        repetitions=0,
        next_review_at=None,
        last_reviewed_at=None,
    )
    defaults.update(kwargs)
    if isinstance(defaults.get("difficulty"), str):
        defaults["difficulty"] = Difficulty(defaults["difficulty"])
    return Doc(**defaults)


def make_exam(**kwargs: Any) -> Doc:
    defaults = _base(
        user_id="",
        subject_id="",
        name="",
        exam_date=date.today(),
        exam_time=None,
        syllabus=None,
        priority=Priority.high,
    )
    defaults.update(kwargs)
    if isinstance(defaults.get("priority"), str):
        defaults["priority"] = Priority(defaults["priority"])
    return Doc(**defaults)


def make_assignment(**kwargs: Any) -> Doc:
    defaults = _base(
        user_id="",
        subject_id=None,
        title="",
        description=None,
        deadline=utcnow(),
        priority=Priority.medium,
        status=AssignmentStatus.pending,
    )
    defaults.update(kwargs)
    if isinstance(defaults.get("priority"), str):
        defaults["priority"] = Priority(defaults["priority"])
    if isinstance(defaults.get("status"), str):
        defaults["status"] = AssignmentStatus(defaults["status"])
    return Doc(**defaults)


def make_recommendation(**kwargs: Any) -> Doc:
    defaults = _base(
        user_id="",
        topic_id=None,
        subject_id=None,
        priority=Priority.medium,
        title="",
        reason="",
        suggested_actions_json="[]",
        score=0.0,
        is_dismissed=False,
    )
    defaults.update(kwargs)
    if isinstance(defaults.get("priority"), str):
        defaults["priority"] = Priority(defaults["priority"])
    return Doc(**defaults)


def make_study_activity(**kwargs: Any) -> Doc:
    defaults = _base(
        user_id="",
        activity_date=date.today(),
        minutes=0,
        activity_type="study",
        subject_id=None,
        topic_id=None,
    )
    defaults.update(kwargs)
    return Doc(**defaults)


def make_password_reset(**kwargs: Any) -> Doc:
    defaults = _base(
        user_id="",
        token_hash="",
        expires_at=utcnow(),
        used=False,
    )
    defaults.update(kwargs)
    return Doc(**defaults)


# Aliases used across the codebase (look like former ORM classes)
User = Doc
StudentProfile = Doc
Subject = Doc
Unit = Doc
Topic = Doc
Document = Doc
DocumentChunk = Doc
Conversation = Doc
Message = Doc
StudyPlan = Doc
StudySession = Doc
Quiz = Doc
QuizQuestion = Doc
QuizAttempt = Doc
QuizAnswer = Doc
Flashcard = Doc
Exam = Doc
Assignment = Doc
Recommendation = Doc
StudyActivity = Doc
PasswordResetToken = Doc
PerformanceRecord = Doc

__all__ = [
    "Doc",
    "from_mongo",
    "touch",
    "utcnow",
    "new_uuid",
    "UserRole",
    "Difficulty",
    "TopicStatus",
    "DocumentStatus",
    "AssignmentStatus",
    "QuestionType",
    "SessionStatus",
    "Priority",
    "make_user",
    "make_profile",
    "make_subject",
    "make_unit",
    "make_topic",
    "make_document",
    "make_chunk",
    "make_conversation",
    "make_message",
    "make_study_plan",
    "make_study_session",
    "make_quiz",
    "make_quiz_question",
    "make_quiz_attempt",
    "make_quiz_answer",
    "make_flashcard",
    "make_exam",
    "make_assignment",
    "make_recommendation",
    "make_study_activity",
    "make_password_reset",
    "User",
    "StudentProfile",
    "Subject",
    "Unit",
    "Topic",
    "Document",
    "DocumentChunk",
    "Conversation",
    "Message",
    "StudyPlan",
    "StudySession",
    "Quiz",
    "QuizQuestion",
    "QuizAttempt",
    "QuizAnswer",
    "Flashcard",
    "Exam",
    "Assignment",
    "Recommendation",
    "StudyActivity",
    "PasswordResetToken",
    "PerformanceRecord",
]
