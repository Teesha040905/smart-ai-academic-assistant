from datetime import date
import json
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.errors import AppError
from app.models import (
    Assignment,
    Exam,
    Flashcard,
    Notification,
    Quiz,
    StudyPlan,
    StudySession,
    User,
)
from app.schemas import (
    AssignmentCreate,
    AssignmentOut,
    AssignmentUpdate,
    ChatMessageCreate,
    ConversationCreate,
    ConversationOut,
    DashboardOut,
    DocumentOut,
    ExamCreate,
    ExamOut,
    ExamUpdate,
    FlashcardGenerateRequest,
    FlashcardOut,
    FlashcardReviewRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MessageOut,
    NotificationOut,
    QuizGenerateRequest,
    QuizOut,
    QuizQuestionOut,
    QuizSubmitRequest,
    QuizAttemptOut,
    RecommendationOut,
    RegisterRequest,
    ResetPasswordRequest,
    SearchResult,
    StudentProfileOut,
    StudentProfileUpdate,
    StudyPlanGenerateRequest,
    StudyPlanOut,
    StudySessionOut,
    StudySessionUpdate,
    SubjectCreate,
    SubjectOut,
    SubjectUpdate,
    SummarizeRequest,
    TopicCreate,
    TopicOut,
    TopicUpdate,
    TokenResponse,
    UnitCreate,
    UnitOut,
    UnitUpdate,
    UserOut,
    UserUpdate,
    AnalyticsOut,
    KnowledgeMapOut,
)
from app.services.auth_service import AuthService
from app.services.subject_service import SubjectService
from app.services.recommendation_service import (
    AnalyticsService,
    RecommendationEngine,
    compute_exam_readiness,
    days_until,
)
from app.services.academic_services import (
    ChatService,
    DocumentService,
    FlashcardService,
    QuizService,
    StudyPlannerService,
)
from app.ai.client import AIClient

router = APIRouter()


def _rec_out(r) -> RecommendationOut:
    return RecommendationOut(
        id=r.id,
        topic_id=r.topic_id,
        subject_id=r.subject_id,
        priority=r.priority,
        title=r.title,
        reason=r.reason,
        suggested_actions=json.loads(r.suggested_actions_json or "[]"),
        score=r.score,
    )


# ── Auth ──────────────────────────────────────────────
@router.post("/auth/register", response_model=UserOut)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    user = AuthService(db).register(data)
    return AuthService(db).get_user_with_profile(user.id)


@router.post("/auth/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    svc = AuthService(db)
    user = svc.authenticate(data.email, data.password)
    return TokenResponse(access_token=svc.issue_token(user))


@router.post("/auth/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    token = AuthService(db).request_password_reset(data.email)
    # Always generic response; include token only in development helper field when found
    payload = {"detail": "If that email exists, a reset link was generated."}
    if token:
        payload["dev_reset_token"] = token
    return payload


@router.post("/auth/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    AuthService(db).reset_password(data.token, data.new_password)
    return {"detail": "Password updated"}


@router.get("/auth/me", response_model=UserOut)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return AuthService(db).get_user_with_profile(user.id)


@router.post("/auth/logout")
def logout(user: User = Depends(get_current_user)):
    return {"detail": "Logged out"}


# ── Users / Profile ───────────────────────────────────
@router.patch("/users/me", response_model=UserOut)
def update_me(data: UserUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    AuthService(db).update_user(user, data)
    return AuthService(db).get_user_with_profile(user.id)


@router.patch("/users/me/profile", response_model=StudentProfileOut)
def update_profile(
    data: StudentProfileUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return AuthService(db).update_profile(user, data)


@router.delete("/users/me")
def delete_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    AuthService(db).delete_account(user)
    return {"detail": "Account deleted"}


# ── Subjects ──────────────────────────────────────────
@router.get("/subjects", response_model=list[SubjectOut])
def list_subjects(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    svc = SubjectService(db)
    return [svc.serialize_subject(s) for s in svc.list_subjects(user)]


@router.post("/subjects", response_model=SubjectOut)
def create_subject(data: SubjectCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    svc = SubjectService(db)
    s = svc.create(user, data)
    return svc.serialize_subject(svc.get_owned(user, s.id))


@router.get("/subjects/{subject_id}", response_model=SubjectOut)
def get_subject(subject_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    svc = SubjectService(db)
    return svc.serialize_subject(svc.get_owned(user, subject_id))


@router.patch("/subjects/{subject_id}", response_model=SubjectOut)
def update_subject(
    subject_id: str, data: SubjectUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    svc = SubjectService(db)
    return svc.serialize_subject(svc.update(user, subject_id, data))


@router.delete("/subjects/{subject_id}")
def delete_subject(subject_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    SubjectService(db).delete(user, subject_id)
    return {"detail": "Deleted"}


@router.post("/subjects/{subject_id}/units", response_model=UnitOut)
def add_unit(
    subject_id: str, data: UnitCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    unit = SubjectService(db).add_unit(user, subject_id, data)
    return {**unit.__dict__, "progress": 0.0, "topics": []}


@router.patch("/units/{unit_id}", response_model=UnitOut)
def update_unit(unit_id: str, data: UnitUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    unit = SubjectService(db).update_unit(user, unit_id, data)
    return {**unit.__dict__, "progress": unit.progress_override or 0.0, "topics": unit.topics}


@router.delete("/units/{unit_id}")
def delete_unit(unit_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    SubjectService(db).delete_unit(user, unit_id)
    return {"detail": "Deleted"}


@router.post("/subjects/{subject_id}/topics", response_model=TopicOut)
def add_topic(
    subject_id: str, data: TopicCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return SubjectService(db).add_topic(user, subject_id, data)


@router.patch("/topics/{topic_id}", response_model=TopicOut)
def update_topic(
    topic_id: str, data: TopicUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return SubjectService(db).update_topic(user, topic_id, data)


@router.delete("/topics/{topic_id}")
def delete_topic(topic_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    SubjectService(db).delete_topic(user, topic_id)
    return {"detail": "Deleted"}


# ── Documents ─────────────────────────────────────────
@router.get("/documents", response_model=list[DocumentOut])
def list_documents(
    q: Optional[str] = None,
    subject_id: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return DocumentService(db).list(user, q=q, subject_id=subject_id)


@router.post("/documents", response_model=DocumentOut)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    subject_id: Optional[str] = Form(None),
    unit_id: Optional[str] = Form(None),
    topic_id: Optional[str] = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return await DocumentService(db).upload(
        user,
        file,
        title=title,
        subject_id=subject_id,
        unit_id=unit_id,
        topic_id=topic_id,
        background=background_tasks,
    )


@router.get("/documents/{document_id}", response_model=DocumentOut)
def get_document(document_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return DocumentService(db).get_owned(user, document_id)


@router.get("/documents/{document_id}/download")
def download_document(document_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    svc = DocumentService(db)
    doc = svc.get_owned(user, document_id)
    path = svc.file_path(doc)
    if not path.exists():
        raise AppError("File missing", status_code=404)
    return FileResponse(path, filename=doc.original_filename, media_type=doc.mime_type)


@router.delete("/documents/{document_id}")
def delete_document(document_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    DocumentService(db).delete(user, document_id)
    return {"detail": "Deleted"}


# ── AI Chat ───────────────────────────────────────────
@router.get("/ai/conversations", response_model=list[ConversationOut])
def list_conversations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    convs = ChatService(db).list_conversations(user)
    return [
        ConversationOut(id=c.id, title=c.title, subject_id=c.subject_id, created_at=c.created_at, messages=[])
        for c in convs
    ]


@router.post("/ai/conversations", response_model=ConversationOut)
def create_conversation(
    data: ConversationCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    c = ChatService(db).create_conversation(user, data.title, data.subject_id)
    return ConversationOut(id=c.id, title=c.title, subject_id=c.subject_id, created_at=c.created_at, messages=[])


@router.get("/ai/conversations/{conversation_id}", response_model=ConversationOut)
def get_conversation(
    conversation_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    c = ChatService(db).get_conversation(user, conversation_id)
    return ConversationOut(
        id=c.id,
        title=c.title,
        subject_id=c.subject_id,
        created_at=c.created_at,
        messages=c.messages,
    )


@router.delete("/ai/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    ChatService(db).delete_conversation(user, conversation_id)
    return {"detail": "Deleted"}


@router.post("/ai/conversations/{conversation_id}/messages", response_model=MessageOut)
def chat_message(
    conversation_id: str,
    data: ChatMessageCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ChatService(db).send_message(user, conversation_id, data)


@router.post("/ai/summarize")
def summarize(data: SummarizeRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    text = data.text or ""
    if data.document_id:
        from app.models import DocumentChunk

        chunks = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == data.document_id, DocumentChunk.user_id == user.id)
            .limit(10)
            .all()
        )
        text = "\n".join(c.content for c in chunks)
    if not text:
        raise AppError("Nothing to summarize", status_code=400)
    ai = AIClient()
    try:
        summary = ai.chat(
            [
                {"role": "system", "content": "Summarize academic material clearly for revision."},
                {"role": "user", "content": text[:12000]},
            ]
        )
    except AppError:
        summary = text[:800] + ("..." if len(text) > 800 else "")
    return {"summary": summary}


# ── Study plans ───────────────────────────────────────
@router.post("/study-plans/generate", response_model=StudyPlanOut)
def generate_plan(
    data: StudyPlanGenerateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    plan = StudyPlannerService(db).generate(user, data)
    plan = (
        db.query(StudyPlan)
        .options(joinedload(StudyPlan.sessions))
        .filter(StudyPlan.id == plan.id)
        .first()
    )
    return plan


@router.get("/study-plans/active", response_model=Optional[StudyPlanOut])
def active_plan(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(StudyPlan)
        .options(joinedload(StudyPlan.sessions))
        .filter(StudyPlan.user_id == user.id, StudyPlan.is_active.is_(True))
        .first()
    )


@router.get("/study-sessions/today", response_model=list[StudySessionOut])
def today_sessions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return StudyPlannerService(db).today_sessions(user)


@router.post("/study-sessions/{session_id}/complete", response_model=StudySessionOut)
def complete_session(session_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return StudyPlannerService(db).complete_session(user, session_id)


@router.post("/study-sessions/{session_id}/miss", response_model=StudyPlanOut)
def miss_session(session_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    plan = StudyPlannerService(db).adapt_after_miss(user, session_id)
    return (
        db.query(StudyPlan)
        .options(joinedload(StudyPlan.sessions))
        .filter(StudyPlan.id == plan.id)
        .first()
    )


@router.patch("/study-sessions/{session_id}", response_model=StudySessionOut)
def update_session(
    session_id: str,
    data: StudySessionUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(StudySession)
        .filter(StudySession.id == session_id, StudySession.user_id == user.id)
        .first()
    )
    if not session:
        raise AppError("Session not found", status_code=404)
    if data.status:
        session.status = data.status
    if data.notes is not None:
        session.notes = data.notes
    db.commit()
    db.refresh(session)
    return session


# ── Quizzes / Flashcards ──────────────────────────────
@router.post("/ai/quiz", response_model=QuizOut)
def generate_quiz(
    data: QuizGenerateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    quiz = QuizService(db).generate(user, data)
    quiz = db.query(Quiz).options(joinedload(Quiz.questions)).filter(Quiz.id == quiz.id).first()
    return QuizOut(
        id=quiz.id,
        title=quiz.title,
        subject_id=quiz.subject_id,
        topic_id=quiz.topic_id,
        difficulty=quiz.difficulty,
        question_count=quiz.question_count,
        questions=[
            QuizQuestionOut(
                id=q.id,
                question_type=q.question_type,
                prompt=q.prompt,
                options_json=q.options_json,
                topic_tag=q.topic_tag,
                order_index=q.order_index,
            )
            for q in sorted(quiz.questions, key=lambda x: x.order_index)
        ],
    )


@router.get("/quizzes", response_model=list[QuizOut])
def list_quizzes(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    quizzes = (
        db.query(Quiz)
        .options(joinedload(Quiz.questions))
        .filter(Quiz.user_id == user.id)
        .order_by(Quiz.created_at.desc())
        .all()
    )
    return [
        QuizOut(
            id=q.id,
            title=q.title,
            subject_id=q.subject_id,
            topic_id=q.topic_id,
            difficulty=q.difficulty,
            question_count=q.question_count,
            questions=[],
        )
        for q in quizzes
    ]


@router.post("/quizzes/{quiz_id}/submit", response_model=QuizAttemptOut)
def submit_quiz(
    quiz_id: str, data: QuizSubmitRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    attempt = QuizService(db).submit(
        user, quiz_id, [a.model_dump() for a in data.answers]
    )
    # Refresh recommendations after quiz
    RecommendationEngine(db).generate(user)
    return attempt


@router.post("/ai/flashcards", response_model=list[FlashcardOut])
def generate_flashcards(
    data: FlashcardGenerateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return FlashcardService(db).generate(user, data)


@router.get("/flashcards", response_model=list[FlashcardOut])
def list_flashcards(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Flashcard)
        .filter(Flashcard.user_id == user.id)
        .order_by(Flashcard.created_at.desc())
        .all()
    )


@router.post("/flashcards/{card_id}/review", response_model=FlashcardOut)
def review_flashcard(
    card_id: str,
    data: FlashcardReviewRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return FlashcardService(db).review(user, card_id, data.rating)


# ── Exams / Assignments ───────────────────────────────
@router.get("/exams", response_model=list[ExamOut])
def list_exams(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    exams = db.query(Exam).filter(Exam.user_id == user.id).order_by(Exam.exam_date).all()
    out = []
    for e in exams:
        out.append(
            ExamOut(
                id=e.id,
                subject_id=e.subject_id,
                name=e.name,
                exam_date=e.exam_date,
                exam_time=e.exam_time,
                syllabus=e.syllabus,
                priority=e.priority,
                days_remaining=days_until(e.exam_date),
                readiness=compute_exam_readiness(db, user, e),
            )
        )
    return out


@router.post("/exams", response_model=ExamOut)
def create_exam(data: ExamCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    exam = Exam(user_id=user.id, **data.model_dump())
    db.add(exam)
    db.commit()
    db.refresh(exam)
    RecommendationEngine(db).generate(user)
    return ExamOut(
        id=exam.id,
        subject_id=exam.subject_id,
        name=exam.name,
        exam_date=exam.exam_date,
        exam_time=exam.exam_time,
        syllabus=exam.syllabus,
        priority=exam.priority,
        days_remaining=days_until(exam.exam_date),
        readiness=compute_exam_readiness(db, user, exam),
    )


@router.patch("/exams/{exam_id}", response_model=ExamOut)
def update_exam(
    exam_id: str, data: ExamUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    exam = db.query(Exam).filter(Exam.id == exam_id, Exam.user_id == user.id).first()
    if not exam:
        raise AppError("Exam not found", status_code=404)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(exam, k, v)
    db.commit()
    db.refresh(exam)
    return ExamOut(
        id=exam.id,
        subject_id=exam.subject_id,
        name=exam.name,
        exam_date=exam.exam_date,
        exam_time=exam.exam_time,
        syllabus=exam.syllabus,
        priority=exam.priority,
        days_remaining=days_until(exam.exam_date),
        readiness=compute_exam_readiness(db, user, exam),
    )


@router.delete("/exams/{exam_id}")
def delete_exam(exam_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    exam = db.query(Exam).filter(Exam.id == exam_id, Exam.user_id == user.id).first()
    if not exam:
        raise AppError("Exam not found", status_code=404)
    db.delete(exam)
    db.commit()
    return {"detail": "Deleted"}


@router.get("/assignments", response_model=list[AssignmentOut])
def list_assignments(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Assignment).filter(Assignment.user_id == user.id).order_by(Assignment.deadline).all()


@router.post("/assignments", response_model=AssignmentOut)
def create_assignment(
    data: AssignmentCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    a = Assignment(user_id=user.id, **data.model_dump())
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


@router.patch("/assignments/{assignment_id}", response_model=AssignmentOut)
def update_assignment(
    assignment_id: str,
    data: AssignmentUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    a = db.query(Assignment).filter(Assignment.id == assignment_id, Assignment.user_id == user.id).first()
    if not a:
        raise AppError("Assignment not found", status_code=404)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(a, k, v)
    db.commit()
    db.refresh(a)
    return a


@router.delete("/assignments/{assignment_id}")
def delete_assignment(
    assignment_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    a = db.query(Assignment).filter(Assignment.id == assignment_id, Assignment.user_id == user.id).first()
    if not a:
        raise AppError("Assignment not found", status_code=404)
    db.delete(a)
    db.commit()
    return {"detail": "Deleted"}


# ── Dashboard / Analytics / Recs / Notifications ───────
@router.get("/dashboard", response_model=DashboardOut)
def dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    analytics = AnalyticsService(db)
    engine = RecommendationEngine(db)
    hour = date.today()  # greeting by clock would need datetime
    from datetime import datetime

    h = datetime.now().hour
    greet = "Good morning" if h < 12 else "Good afternoon" if h < 17 else "Good evening"
    rec = engine.top_recommendation(user)
    exams = db.query(Exam).filter(Exam.user_id == user.id).order_by(Exam.exam_date).limit(3).all()
    assignments = (
        db.query(Assignment)
        .filter(Assignment.user_id == user.id)
        .order_by(Assignment.deadline)
        .limit(5)
        .all()
    )
    return DashboardOut(
        greeting=greet,
        student_name=user.full_name.split()[0],
        stats=analytics.dashboard_stats(user),
        today_plan=StudyPlannerService(db).today_sessions(user),
        weak_topics=engine.weak_topics(user),
        recommendation=_rec_out(rec) if rec else None,
        upcoming_exams=[
            ExamOut(
                id=e.id,
                subject_id=e.subject_id,
                name=e.name,
                exam_date=e.exam_date,
                exam_time=e.exam_time,
                syllabus=e.syllabus,
                priority=e.priority,
                days_remaining=days_until(e.exam_date),
                readiness=compute_exam_readiness(db, user, e),
            )
            for e in exams
        ],
        upcoming_assignments=assignments,
        streak=analytics.study_streak(user),
    )


@router.get("/performance", response_model=AnalyticsOut)
def performance(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return AnalyticsService(db).full_analytics(user)


@router.get("/knowledge-map", response_model=KnowledgeMapOut)
def knowledge_map(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return AnalyticsService(db).knowledge_map(user)


@router.get("/recommendations", response_model=list[RecommendationOut])
def recommendations(
    refresh: bool = False, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    engine = RecommendationEngine(db)
    if refresh:
        recs = engine.generate(user)
    else:
        from app.models import Recommendation

        recs = (
            db.query(Recommendation)
            .filter(Recommendation.user_id == user.id, Recommendation.is_dismissed.is_(False))
            .order_by(Recommendation.score.desc())
            .all()
        )
        if not recs:
            recs = engine.generate(user)
    return [_rec_out(r) for r in recs]


@router.get("/notifications", response_model=list[NotificationOut])
def list_notifications(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Notification)
        .filter(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )


@router.post("/notifications/{notification_id}/read", response_model=NotificationOut)
def read_notification(
    notification_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    n = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user.id)
        .first()
    )
    if not n:
        raise AppError("Not found", status_code=404)
    n.is_read = True
    db.commit()
    db.refresh(n)
    return n


@router.get("/search", response_model=list[SearchResult])
def search(q: str = Query(min_length=1), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models import Document, Subject, Topic

    like = f"%{q}%"
    results: list[SearchResult] = []
    for s in db.query(Subject).filter(Subject.user_id == user.id, Subject.name.ilike(like)).limit(10):
        results.append(SearchResult(type="subject", id=s.id, title=s.name, subtitle=s.code))
    for t in db.query(Topic).filter(Topic.user_id == user.id, Topic.name.ilike(like)).limit(10):
        results.append(SearchResult(type="topic", id=t.id, title=t.name, subtitle="Topic"))
    for d in db.query(Document).filter(Document.user_id == user.id, Document.title.ilike(like)).limit(10):
        results.append(SearchResult(type="document", id=d.id, title=d.title, subtitle=d.original_filename))
    for f in db.query(Flashcard).filter(Flashcard.user_id == user.id, Flashcard.question.ilike(like)).limit(10):
        results.append(SearchResult(type="flashcard", id=f.id, title=f.question[:80], subtitle="Flashcard"))
    for a in db.query(Assignment).filter(Assignment.user_id == user.id, Assignment.title.ilike(like)).limit(10):
        results.append(SearchResult(type="assignment", id=a.id, title=a.title, subtitle="Assignment"))
    return results
