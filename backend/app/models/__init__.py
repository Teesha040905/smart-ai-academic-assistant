import enum
from datetime import date, datetime, time
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey, new_uuid


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


class User(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.student, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    theme: Mapped[str] = mapped_column(String(20), default="system", nullable=False)

    profile: Mapped[Optional["StudentProfile"]] = relationship(back_populates="user", uselist=False)
    subjects: Mapped[list["Subject"]] = relationship(back_populates="user")


class StudentProfile(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "student_profiles"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    photo_url: Mapped[Optional[str]] = mapped_column(String(500))
    course: Mapped[Optional[str]] = mapped_column(String(120))
    branch: Mapped[Optional[str]] = mapped_column(String(120))
    semester: Mapped[Optional[int]] = mapped_column(Integer)
    academic_year: Mapped[Optional[str]] = mapped_column(String(40))
    preferred_study_time: Mapped[Optional[str]] = mapped_column(String(40))  # morning/afternoon/evening
    daily_study_hours: Mapped[float] = mapped_column(Float, default=3.0)
    learning_preferences: Mapped[Optional[str]] = mapped_column(Text)  # JSON string
    academic_goals: Mapped[Optional[str]] = mapped_column(Text)
    notification_prefs: Mapped[Optional[str]] = mapped_column(Text)  # JSON
    ai_prefs: Mapped[Optional[str]] = mapped_column(Text)  # JSON

    user: Mapped["User"] = relationship(back_populates="profile")


class Subject(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "subjects"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(40))
    description: Mapped[Optional[str]] = mapped_column(Text)
    color: Mapped[str] = mapped_column(String(20), default="#2563eb")
    priority: Mapped[Priority] = mapped_column(Enum(Priority), default=Priority.medium)
    exam_date: Mapped[Optional[date]] = mapped_column(Date)

    user: Mapped["User"] = relationship(back_populates="subjects")
    units: Mapped[list["Unit"]] = relationship(back_populates="subject", cascade="all, delete-orphan")
    topics: Mapped[list["Topic"]] = relationship(back_populates="subject", cascade="all, delete-orphan")


class Unit(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "units"

    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    progress_override: Mapped[Optional[float]] = mapped_column(Float)  # optional manual %

    subject: Mapped["Subject"] = relationship(back_populates="units")
    topics: Mapped[list["Topic"]] = relationship(back_populates="unit", cascade="all, delete-orphan")


class Topic(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "topics"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), index=True)
    unit_id: Mapped[Optional[str]] = mapped_column(ForeignKey("units.id", ondelete="SET NULL"), index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    difficulty: Mapped[Difficulty] = mapped_column(Enum(Difficulty), default=Difficulty.medium)
    status: Mapped[TopicStatus] = mapped_column(Enum(TopicStatus), default=TopicStatus.not_started)
    knowledge_level: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100
    last_studied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    revision_count: Mapped[int] = mapped_column(Integer, default=0)
    quiz_average: Mapped[Optional[float]] = mapped_column(Float)
    importance: Mapped[float] = mapped_column(Float, default=1.0)

    subject: Mapped["Subject"] = relationship(back_populates="topics")
    unit: Mapped[Optional["Unit"]] = relationship(back_populates="topics")


class Document(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "documents"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    subject_id: Mapped[Optional[str]] = mapped_column(ForeignKey("subjects.id", ondelete="SET NULL"))
    unit_id: Mapped[Optional[str]] = mapped_column(ForeignKey("units.id", ondelete="SET NULL"))
    topic_id: Mapped[Optional[str]] = mapped_column(ForeignKey("topics.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(300), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(300), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(120), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(Enum(DocumentStatus), default=DocumentStatus.pending)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    page_count: Mapped[Optional[int]] = mapped_column(Integer)

    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class DocumentChunk(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "document_chunks"

    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[Optional[int]] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    vector_id: Mapped[Optional[str]] = mapped_column(String(100))
    token_estimate: Mapped[int] = mapped_column(Integer, default=0)

    document: Mapped["Document"] = relationship(back_populates="chunks")


class Conversation(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "conversations"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200), default="New conversation")
    subject_id: Mapped[Optional[str]] = mapped_column(ForeignKey("subjects.id", ondelete="SET NULL"))

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at"
    )


class Message(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "messages"

    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user | assistant | system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources_json: Mapped[Optional[str]] = mapped_column(Text)  # citation metadata
    used_rag: Mapped[bool] = mapped_column(Boolean, default=False)
    from_general_knowledge: Mapped[bool] = mapped_column(Boolean, default=False)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


class StudyPlan(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "study_plans"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200), default="Adaptive Study Plan")
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    sessions: Mapped[list["StudySession"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan"
    )


class StudySession(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "study_sessions"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    plan_id: Mapped[Optional[str]] = mapped_column(ForeignKey("study_plans.id", ondelete="SET NULL"))
    subject_id: Mapped[Optional[str]] = mapped_column(ForeignKey("subjects.id", ondelete="SET NULL"))
    topic_id: Mapped[Optional[str]] = mapped_column(ForeignKey("topics.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[Optional[time]] = mapped_column(Time)
    end_time: Mapped[Optional[time]] = mapped_column(Time)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    status: Mapped[SessionStatus] = mapped_column(Enum(SessionStatus), default=SessionStatus.planned)
    activity_type: Mapped[str] = mapped_column(String(40), default="study")  # study|revision|quiz|flashcards
    notes: Mapped[Optional[str]] = mapped_column(Text)

    plan: Mapped[Optional["StudyPlan"]] = relationship(back_populates="sessions")


class Quiz(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "quizzes"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    subject_id: Mapped[Optional[str]] = mapped_column(ForeignKey("subjects.id", ondelete="SET NULL"))
    unit_id: Mapped[Optional[str]] = mapped_column(ForeignKey("units.id", ondelete="SET NULL"))
    topic_id: Mapped[Optional[str]] = mapped_column(ForeignKey("topics.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    difficulty: Mapped[Difficulty] = mapped_column(Enum(Difficulty), default=Difficulty.medium)
    question_count: Mapped[int] = mapped_column(Integer, default=10)

    questions: Mapped[list["QuizQuestion"]] = relationship(
        back_populates="quiz", cascade="all, delete-orphan"
    )
    attempts: Mapped[list["QuizAttempt"]] = relationship(
        back_populates="quiz", cascade="all, delete-orphan"
    )


class QuizQuestion(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "quiz_questions"

    quiz_id: Mapped[str] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"), index=True)
    question_type: Mapped[QuestionType] = mapped_column(Enum(QuestionType), default=QuestionType.mcq)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    options_json: Mapped[Optional[str]] = mapped_column(Text)  # for MCQ
    correct_answer: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text)
    topic_tag: Mapped[Optional[str]] = mapped_column(String(200))
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    quiz: Mapped["Quiz"] = relationship(back_populates="questions")


class QuizAttempt(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "quiz_attempts"

    quiz_id: Mapped[str] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    max_score: Mapped[float] = mapped_column(Float, default=0.0)
    percentage: Mapped[float] = mapped_column(Float, default=0.0)
    strong_topics_json: Mapped[Optional[str]] = mapped_column(Text)
    weak_topics_json: Mapped[Optional[str]] = mapped_column(Text)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    quiz: Mapped["Quiz"] = relationship(back_populates="attempts")
    answers: Mapped[list["QuizAnswer"]] = relationship(
        back_populates="attempt", cascade="all, delete-orphan"
    )


class QuizAnswer(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "quiz_answers"

    attempt_id: Mapped[str] = mapped_column(ForeignKey("quiz_attempts.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("quiz_questions.id", ondelete="CASCADE"))
    user_answer: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)

    attempt: Mapped["QuizAttempt"] = relationship(back_populates="answers")


class Flashcard(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "flashcards"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    subject_id: Mapped[Optional[str]] = mapped_column(ForeignKey("subjects.id", ondelete="SET NULL"))
    topic_id: Mapped[Optional[str]] = mapped_column(ForeignKey("topics.id", ondelete="SET NULL"))
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[Difficulty] = mapped_column(Enum(Difficulty), default=Difficulty.medium)
    review_status: Mapped[str] = mapped_column(String(40), default="new")
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5)
    interval_days: Mapped[int] = mapped_column(Integer, default=0)
    repetitions: Mapped[int] = mapped_column(Integer, default=0)
    next_review_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class Exam(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "exams"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    exam_date: Mapped[date] = mapped_column(Date, nullable=False)
    exam_time: Mapped[Optional[time]] = mapped_column(Time)
    syllabus: Mapped[Optional[str]] = mapped_column(Text)
    priority: Mapped[Priority] = mapped_column(Enum(Priority), default=Priority.high)


class Assignment(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "assignments"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    subject_id: Mapped[Optional[str]] = mapped_column(ForeignKey("subjects.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    priority: Mapped[Priority] = mapped_column(Enum(Priority), default=Priority.medium)
    status: Mapped[AssignmentStatus] = mapped_column(
        Enum(AssignmentStatus), default=AssignmentStatus.pending
    )


class Notification(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "notifications"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(40), default="general")
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    link: Mapped[Optional[str]] = mapped_column(String(300))


class Recommendation(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "recommendations"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    topic_id: Mapped[Optional[str]] = mapped_column(ForeignKey("topics.id", ondelete="SET NULL"))
    subject_id: Mapped[Optional[str]] = mapped_column(ForeignKey("subjects.id", ondelete="SET NULL"))
    priority: Mapped[Priority] = mapped_column(Enum(Priority), default=Priority.medium)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_actions_json: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False)


class StudyActivity(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "study_activities"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    activity_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    minutes: Mapped[int] = mapped_column(Integer, default=0)
    activity_type: Mapped[str] = mapped_column(String(40), default="study")
    subject_id: Mapped[Optional[str]] = mapped_column(ForeignKey("subjects.id", ondelete="SET NULL"))
    topic_id: Mapped[Optional[str]] = mapped_column(ForeignKey("topics.id", ondelete="SET NULL"))

    __table_args__ = (UniqueConstraint("user_id", "activity_date", "activity_type", "topic_id"),)


class PerformanceRecord(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "performance_records"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    subject_id: Mapped[Optional[str]] = mapped_column(ForeignKey("subjects.id", ondelete="SET NULL"))
    topic_id: Mapped[Optional[str]] = mapped_column(ForeignKey("topics.id", ondelete="SET NULL"))
    metric: Mapped[str] = mapped_column(String(80), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PasswordResetToken(Base, UUIDPrimaryKey, TimestampMixin):
    """Architecture for forgot-password; email delivery can be wired later."""

    __tablename__ = "password_reset_tokens"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False)
