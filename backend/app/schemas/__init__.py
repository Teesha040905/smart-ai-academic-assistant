import re
from datetime import date, datetime, time
from typing import Annotated, Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator

from app.models import (
    AssignmentStatus,
    Difficulty,
    DocumentStatus,
    Priority,
    QuestionType,
    SessionStatus,
    TopicStatus,
    UserRole,
)

T = TypeVar("T")

# Trimmed, non-blank display name (units, topics, exams, assignments)
NameStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
HexColor = Annotated[str, StringConstraints(pattern=r"^#(?:[0-9a-fA-F]{3}){1,2}$")]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Paginated(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int


# ── Auth ──────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


# ── Profile ───────────────────────────────────────────
class StudentProfileUpdate(BaseModel):
    photo_url: Optional[str] = None
    course: Optional[str] = None
    branch: Optional[str] = None
    semester: Optional[int] = Field(default=None, ge=1, le=12)
    academic_year: Optional[str] = None
    preferred_study_time: Optional[str] = None
    daily_study_hours: Optional[float] = Field(default=None, ge=0.5, le=16)
    learning_preferences: Optional[str] = None
    academic_goals: Optional[str] = None
    notification_prefs: Optional[str] = None
    ai_prefs: Optional[str] = None


class StudentProfileOut(ORMModel):
    id: str
    user_id: str
    photo_url: Optional[str] = None
    course: Optional[str] = None
    branch: Optional[str] = None
    semester: Optional[int] = None
    academic_year: Optional[str] = None
    preferred_study_time: Optional[str] = None
    daily_study_hours: float
    learning_preferences: Optional[str] = None
    academic_goals: Optional[str] = None
    notification_prefs: Optional[str] = None
    ai_prefs: Optional[str] = None


class UserOut(ORMModel):
    id: str
    email: EmailStr
    full_name: str
    role: UserRole
    theme: str
    is_active: bool
    profile: Optional[StudentProfileOut] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    theme: Optional[str] = None


# ── Subjects / Units / Topics ──────────────────────────
_SUBJECT_NAME_CHARS = re.compile(r"^[A-Za-z0-9 &()+#.,'/:-]+$")


def validate_subject_name(value: str) -> str:
    """Reject names that can't be a real subject: bare numbers, symbols, or repeated characters."""
    name = " ".join(value.split())
    has_letter = any(c.isalpha() for c in name)
    if len(name) < 2 or len(name) > 100:
        raise ValueError("Subject name must be between 2 and 100 characters")
    if not _SUBJECT_NAME_CHARS.match(name):
        raise ValueError("Subject name contains invalid characters")
    if not has_letter:
        raise ValueError("Subject name must contain letters, not just numbers or symbols")
    if len(set(name.lower().replace(" ", ""))) == 1:
        raise ValueError("Please enter a valid subject name")
    return name


class SubjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    code: Optional[str] = None
    description: Optional[str] = None
    color: HexColor = "#2563eb"
    priority: Priority = Priority.medium
    exam_date: Optional[date] = None

    @field_validator("name")
    @classmethod
    def _check_name(cls, value: str) -> str:
        return validate_subject_name(value)


class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    color: Optional[HexColor] = None
    priority: Optional[Priority] = None
    exam_date: Optional[date] = None

    @field_validator("name")
    @classmethod
    def _check_name(cls, value: Optional[str]) -> Optional[str]:
        return None if value is None else validate_subject_name(value)


class UnitCreate(BaseModel):
    name: NameStr
    order_index: int = 0


class UnitUpdate(BaseModel):
    name: Optional[NameStr] = None
    order_index: Optional[int] = None
    progress_override: Optional[float] = Field(default=None, ge=0, le=100)


class TopicCreate(BaseModel):
    name: NameStr
    description: Optional[str] = None
    unit_id: Optional[str] = None
    difficulty: Difficulty = Difficulty.medium
    importance: float = Field(default=1.0, gt=0, le=10)


class TopicUpdate(BaseModel):
    name: Optional[NameStr] = None
    description: Optional[str] = None
    unit_id: Optional[str] = None
    difficulty: Optional[Difficulty] = None
    status: Optional[TopicStatus] = None
    knowledge_level: Optional[float] = Field(default=None, ge=0, le=100)
    importance: Optional[float] = Field(default=None, gt=0, le=10)


class TopicOut(ORMModel):
    id: str
    subject_id: str
    unit_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    difficulty: Difficulty
    status: TopicStatus
    knowledge_level: float
    last_studied_at: Optional[datetime] = None
    revision_count: int
    quiz_average: Optional[float] = None
    importance: float


class UnitOut(ORMModel):
    id: str
    subject_id: str
    name: str
    order_index: int
    progress_override: Optional[float] = None
    progress: float = 0.0
    topics: List[TopicOut] = []


class SubjectOut(ORMModel):
    id: str
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    color: str
    priority: Priority
    exam_date: Optional[date] = None
    progress: float = 0.0
    units: List[UnitOut] = []
    topics: List[TopicOut] = []


# ── Documents ──────────────────────────────────────────
class DocumentOut(ORMModel):
    id: str
    title: str
    original_filename: str
    mime_type: str
    file_size: int
    status: DocumentStatus
    progress: int
    error_message: Optional[str] = None
    subject_id: Optional[str] = None
    unit_id: Optional[str] = None
    topic_id: Optional[str] = None
    page_count: Optional[int] = None
    created_at: datetime


# ── Chat ───────────────────────────────────────────────
class ChatMessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=8000)
    use_rag: bool = True
    subject_id: Optional[str] = None
    document_id: Optional[str] = None


class ConversationCreate(BaseModel):
    title: str = "New conversation"
    subject_id: Optional[str] = None


class MessageOut(ORMModel):
    id: str
    role: str
    content: str
    sources_json: Optional[str] = None
    used_rag: bool
    from_general_knowledge: bool
    created_at: datetime


class ConversationOut(ORMModel):
    id: str
    title: str
    subject_id: Optional[str] = None
    created_at: datetime
    messages: List[MessageOut] = []


# ── Study plan ─────────────────────────────────────────
class StudyPlanGenerateRequest(BaseModel):
    days: int = Field(default=7, ge=1, le=30)
    hours_per_day: Optional[float] = None
    prefer_weak_topics: bool = True


class StudySessionUpdate(BaseModel):
    status: Optional[SessionStatus] = None
    notes: Optional[str] = None


class StudySessionOut(ORMModel):
    id: str
    plan_id: Optional[str] = None
    subject_id: Optional[str] = None
    topic_id: Optional[str] = None
    title: str
    scheduled_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    duration_minutes: int
    status: SessionStatus
    activity_type: str
    notes: Optional[str] = None


class StudyPlanOut(ORMModel):
    id: str
    title: str
    start_date: date
    end_date: date
    notes: Optional[str] = None
    is_active: bool
    sessions: List[StudySessionOut] = []


# ── Quiz ───────────────────────────────────────────────
class QuizGenerateRequest(BaseModel):
    subject_id: Optional[str] = None
    unit_id: Optional[str] = None
    topic_id: Optional[str] = None
    number_of_questions: int = Field(default=10, ge=1, le=30)
    difficulty: Difficulty = Difficulty.medium
    question_types: List[QuestionType] = [QuestionType.mcq]
    adaptive: bool = True


class QuizAnswerSubmit(BaseModel):
    question_id: str
    user_answer: str


class QuizSubmitRequest(BaseModel):
    answers: List[QuizAnswerSubmit]


class QuizQuestionOut(ORMModel):
    id: str
    question_type: QuestionType
    prompt: str
    options_json: Optional[str] = None
    topic_tag: Optional[str] = None
    order_index: int
    # correct_answer hidden until after attempt unless include_answers


class QuizQuestionReviewOut(QuizQuestionOut):
    correct_answer: str
    explanation: Optional[str] = None


class QuizOut(ORMModel):
    id: str
    title: str
    subject_id: Optional[str] = None
    topic_id: Optional[str] = None
    difficulty: Difficulty
    question_count: int
    questions: List[QuizQuestionOut] = []


class QuizAnswerReview(BaseModel):
    question_id: str
    user_answer: str
    correct_answer: str
    is_correct: bool
    explanation: Optional[str] = None


class QuizAttemptOut(ORMModel):
    id: str
    quiz_id: str
    score: float
    max_score: float
    percentage: float
    strong_topics_json: Optional[str] = None
    weak_topics_json: Optional[str] = None
    completed_at: Optional[datetime] = None
    review: List[QuizAnswerReview] = []


# ── Flashcards ─────────────────────────────────────────
class FlashcardGenerateRequest(BaseModel):
    subject_id: Optional[str] = None
    topic_id: Optional[str] = None
    document_id: Optional[str] = None
    count: int = Field(default=10, ge=1, le=40)
    from_quiz_mistakes: bool = False


class FlashcardReviewRequest(BaseModel):
    rating: str = Field(pattern="^(easy|medium|hard)$")


class FlashcardOut(ORMModel):
    id: str
    subject_id: Optional[str] = None
    topic_id: Optional[str] = None
    question: str
    answer: str
    difficulty: Difficulty
    review_status: str
    next_review_at: Optional[datetime] = None


# ── Exams / Assignments ────────────────────────────────
class ExamCreate(BaseModel):
    subject_id: str
    name: NameStr
    exam_date: date
    exam_time: Optional[time] = None
    syllabus: Optional[str] = None
    priority: Priority = Priority.high


class ExamUpdate(BaseModel):
    name: Optional[NameStr] = None
    exam_date: Optional[date] = None
    exam_time: Optional[time] = None
    syllabus: Optional[str] = None
    priority: Optional[Priority] = None


class ExamOut(ORMModel):
    id: str
    subject_id: str
    name: str
    exam_date: date
    exam_time: Optional[time] = None
    syllabus: Optional[str] = None
    priority: Priority
    days_remaining: Optional[int] = None
    readiness: Optional[dict[str, Any]] = None


class AssignmentCreate(BaseModel):
    title: NameStr
    subject_id: Optional[str] = None
    description: Optional[str] = None
    deadline: datetime
    priority: Priority = Priority.medium


class AssignmentUpdate(BaseModel):
    title: Optional[NameStr] = None
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    priority: Optional[Priority] = None
    status: Optional[AssignmentStatus] = None
    subject_id: Optional[str] = None


class AssignmentOut(ORMModel):
    id: str
    title: str
    subject_id: Optional[str] = None
    description: Optional[str] = None
    deadline: datetime
    priority: Priority
    status: AssignmentStatus


# ── Recommendations / Analytics ──────────────────────
class RecommendationOut(ORMModel):
    id: str
    topic_id: Optional[str] = None
    subject_id: Optional[str] = None
    priority: Priority
    title: str
    reason: str
    suggested_actions: List[dict[str, Any]] = []
    score: float


class DashboardOut(BaseModel):
    greeting: str
    student_name: str
    stats: dict[str, Any]
    today_plan: List[StudySessionOut]
    weak_topics: List[dict[str, Any]]
    recommendation: Optional[RecommendationOut] = None
    upcoming_exams: List[ExamOut] = []
    upcoming_assignments: List[AssignmentOut] = []
    streak: dict[str, Any]


class AnalyticsOut(BaseModel):
    overall_progress: float
    subject_performance: List[dict[str, Any]]
    topic_performance: List[dict[str, Any]]
    study_hours: float
    quiz_average: float
    assignments_completed: int
    topics_completed: int
    topics_remaining: int
    weekly_progress: List[dict[str, Any]]
    monthly_progress: List[dict[str, Any]]
    revision_frequency: float
    study_consistency: float


class KnowledgeMapOut(BaseModel):
    subjects: List[dict[str, Any]]


class SearchResult(BaseModel):
    type: str
    id: str
    title: str
    subtitle: Optional[str] = None


class SummarizeRequest(BaseModel):
    document_id: Optional[str] = None
    topic_id: Optional[str] = None
    text: Optional[str] = None
