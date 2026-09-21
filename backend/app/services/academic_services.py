from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import BackgroundTasks, UploadFile
from sqlalchemy.orm import Session

from app.ai.client import AIClient
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.logging import get_logger
from app.models import (
    Conversation,
    Difficulty,
    Document,
    DocumentChunk,
    DocumentStatus,
    Flashcard,
    Message,
    QuestionType,
    Quiz,
    QuizAnswer,
    QuizAttempt,
    QuizQuestion,
    SessionStatus,
    StudyActivity,
    StudyPlan,
    StudySession,
    Topic,
    TopicStatus,
    User,
)
from app.rag.pipeline import RAGService, chunk_text, clean_text, extract_text
from app.schemas import (
    ChatMessageCreate,
    FlashcardGenerateRequest,
    QuizGenerateRequest,
    StudyPlanGenerateRequest,
)

logger = get_logger(__name__)
settings = get_settings()


ALLOWED_MIME = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.ms-powerpoint",
    "text/plain",
    "image/png",
    "image/jpeg",
    "image/webp",
}


class DocumentService:
    def __init__(self, db: Session):
        self.db = db
        self.upload_root = Path(settings.upload_dir)
        self.upload_root.mkdir(parents=True, exist_ok=True)

    def list(self, user: User, q: Optional[str] = None, subject_id: Optional[str] = None) -> list[Document]:
        query = self.db.query(Document).filter(Document.user_id == user.id)
        if subject_id:
            query = query.filter(Document.subject_id == subject_id)
        if q:
            like = f"%{q}%"
            query = query.filter(Document.title.ilike(like) | Document.original_filename.ilike(like))
        return query.order_by(Document.created_at.desc()).all()

    def get_owned(self, user: User, document_id: str) -> Document:
        doc = self.db.query(Document).filter(Document.id == document_id, Document.user_id == user.id).first()
        if not doc:
            raise AppError("Document not found", status_code=404)
        return doc

    async def upload(
        self,
        user: User,
        file: UploadFile,
        *,
        title: Optional[str] = None,
        subject_id: Optional[str] = None,
        unit_id: Optional[str] = None,
        topic_id: Optional[str] = None,
        background: Optional[BackgroundTasks] = None,
    ) -> Document:
        filename = file.filename or "upload.bin"
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in settings.allowed_extension_set:
            raise AppError("File type not allowed", status_code=400, code="invalid_file")
        content = await file.read()
        max_bytes = settings.max_upload_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise AppError(f"File exceeds {settings.max_upload_mb}MB limit", status_code=400)
        mime = file.content_type or "application/octet-stream"
        safe_name = f"{uuid4().hex}.{ext}"
        user_dir = self.upload_root / user.id
        user_dir.mkdir(parents=True, exist_ok=True)
        dest = user_dir / safe_name
        dest.write_bytes(content)

        doc = Document(
            user_id=user.id,
            subject_id=subject_id,
            unit_id=unit_id,
            topic_id=topic_id,
            title=title or filename,
            original_filename=filename,
            stored_filename=str(dest.relative_to(self.upload_root)).replace("\\", "/"),
            mime_type=mime,
            file_size=len(content),
            status=DocumentStatus.pending,
            progress=0,
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)

        if background:
            background.add_task(process_document_job, doc.id)
        else:
            process_document_job(doc.id)
        return doc

    def delete(self, user: User, document_id: str) -> None:
        doc = self.get_owned(user, document_id)
        RAGService().store.delete_document(doc.id, user.id)
        path = self.upload_root / doc.stored_filename
        if path.exists():
            path.unlink(missing_ok=True)
        self.db.delete(doc)
        self.db.commit()

    def file_path(self, doc: Document) -> Path:
        return self.upload_root / doc.stored_filename


def process_document_job(document_id: str) -> None:
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        doc = db.get(Document, document_id)
        if not doc:
            return
        doc.status = DocumentStatus.processing
        doc.progress = 10
        db.commit()

        path = Path(settings.upload_dir) / doc.stored_filename
        raw, page_count = extract_text(path, doc.mime_type)
        text = clean_text(raw)
        doc.page_count = page_count
        doc.progress = 40
        db.commit()

        chunks = chunk_text(text)
        if not chunks:
            doc.status = DocumentStatus.failed
            doc.error_message = "No extractable text found"
            db.commit()
            return

        ai = AIClient()
        rag = RAGService()
        # Delete previous vectors
        rag.store.delete_document(doc.id, doc.user_id)
        db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()

        contents = [c["content"] for c in chunks]
        # Embed in batches
        embeddings: list[list[float]] = []
        batch = 32
        for i in range(0, len(contents), batch):
            embeddings.extend(ai.embed(contents[i : i + batch]))
            doc.progress = 40 + int(50 * (i + batch) / max(len(contents), 1))
            db.commit()

        ids = []
        metadatas = []
        db_chunks = []
        for i, c in enumerate(chunks):
            chunk_id = str(uuid4())
            ids.append(chunk_id)
            metadatas.append(
                {
                    "user_id": doc.user_id,
                    "document_id": doc.id,
                    "subject_id": doc.subject_id or "",
                    "topic_id": doc.topic_id or "",
                    "chunk_id": chunk_id,
                    "page_number": c["page_number"] or 0,
                    "document_title": doc.title,
                }
            )
            db_chunks.append(
                DocumentChunk(
                    id=chunk_id,
                    document_id=doc.id,
                    user_id=doc.user_id,
                    chunk_index=c["chunk_index"],
                    page_number=c["page_number"],
                    content=c["content"],
                    vector_id=chunk_id,
                    token_estimate=c["token_estimate"],
                )
            )

        rag.store.upsert_chunks(ids=ids, embeddings=embeddings, documents=contents, metadatas=metadatas)
        db.add_all(db_chunks)
        doc.status = DocumentStatus.ready
        doc.progress = 100
        doc.error_message = None
        db.commit()
        logger.info("document_processed document_id=%s chunks=%s", doc.id, len(chunks))
    except Exception as exc:
        logger.exception("document_processing_failed document_id=%s", document_id)
        doc = db.get(Document, document_id)
        if doc:
            doc.status = DocumentStatus.failed
            doc.error_message = str(exc)[:500]
            db.commit()
    finally:
        db.close()


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.ai = AIClient()
        self.rag = RAGService()

    def list_conversations(self, user: User) -> list[Conversation]:
        return (
            self.db.query(Conversation)
            .filter(Conversation.user_id == user.id)
            .order_by(Conversation.updated_at.desc())
            .all()
        )

    def get_conversation(self, user: User, conversation_id: str) -> Conversation:
        conv = (
            self.db.query(Conversation)
            .filter(Conversation.id == conversation_id, Conversation.user_id == user.id)
            .first()
        )
        if not conv:
            raise AppError("Conversation not found", status_code=404)
        return conv

    def create_conversation(self, user: User, title: str = "New conversation", subject_id: Optional[str] = None) -> Conversation:
        conv = Conversation(user_id=user.id, title=title, subject_id=subject_id)
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def delete_conversation(self, user: User, conversation_id: str) -> None:
        conv = self.get_conversation(user, conversation_id)
        self.db.delete(conv)
        self.db.commit()

    def send_message(self, user: User, conversation_id: str, data: ChatMessageCreate) -> Message:
        conv = self.get_conversation(user, conversation_id)
        user_msg = Message(
            conversation_id=conv.id,
            user_id=user.id,
            role="user",
            content=data.content,
        )
        self.db.add(user_msg)

        sources: list[dict] = []
        used_rag = False
        from_general = True
        context = ""

        if data.use_rag:
            hits = self.rag.retrieve(
                user_id=user.id,
                query=data.content,
                document_id=data.document_id,
                subject_id=data.subject_id or conv.subject_id,
            )
            context, sources, used_rag = self.rag.build_context(hits)
            from_general = not bool(context)

        system = (
            "You are an academic tutor for university students. "
            "Prefer the student's uploaded study materials when provided. "
            "If context is provided, ground answers in it and cite sources by title/page. "
            "Never invent document page references. "
            "If context is insufficient, say clearly that you are using general knowledge."
        )
        history = (
            self.db.query(Message)
            .filter(Message.conversation_id == conv.id)
            .order_by(Message.created_at.asc())
            .all()
        )
        messages = [{"role": "system", "content": system}]
        for m in history[-12:]:
            messages.append({"role": m.role, "content": m.content})
        messages.append({"role": "user", "content": data.content})
        if context:
            messages.insert(
                1,
                {
                    "role": "system",
                    "content": f"Relevant excerpts from the student's materials:\n\n{context}",
                },
            )

        try:
            answer = self.ai.chat(messages)
        except AppError as exc:
            if exc.code == "ai_unavailable" and context:
                answer = (
                    "AI is temporarily unavailable. Here are the most relevant excerpts "
                    "from your materials:\n\n" + context
                )
                from_general = False
            elif exc.code == "ai_unavailable":
                answer = (
                    "AI is not available right now. Configure AI_API_KEY or try again later. "
                    "Your study data is safe."
                )
            else:
                raise

        if from_general and used_rag is False:
            answer = (
                "_Note: This answer uses general AI knowledge because matching material "
                "was not found in your uploads._\n\n" + answer
            )
        elif from_general and used_rag:
            answer = (
                "_Note: Retrieved materials were weakly related; parts may use general knowledge._\n\n"
                + answer
            )

        if conv.title == "New conversation":
            conv.title = data.content[:60]

        assistant = Message(
            conversation_id=conv.id,
            user_id=user.id,
            role="assistant",
            content=answer,
            sources_json=json.dumps(sources) if sources else None,
            used_rag=bool(sources),
            from_general_knowledge=from_general,
        )
        self.db.add(assistant)
        self.db.commit()
        self.db.refresh(assistant)
        return assistant


class StudyPlannerService:
    def __init__(self, db: Session):
        self.db = db

    def generate(self, user: User, data: StudyPlanGenerateRequest) -> StudyPlan:
        hours = data.hours_per_day or (user.profile.daily_study_hours if user.profile else 3.0)
        minutes_budget = int(hours * 60)
        prefer = user.profile.preferred_study_time if user.profile else "evening"
        start_map = {"morning": time(7, 0), "afternoon": time(14, 0), "evening": time(18, 0)}
        base_start = start_map.get((prefer or "evening").lower(), time(18, 0))

        # Deactivate old plans
        for p in self.db.query(StudyPlan).filter(StudyPlan.user_id == user.id, StudyPlan.is_active.is_(True)):
            p.is_active = False

        start = date.today()
        end = start + timedelta(days=data.days - 1)
        plan = StudyPlan(
            user_id=user.id,
            title="Adaptive Study Plan",
            start_date=start,
            end_date=end,
            notes="Generated from exam urgency, weak topics, and available hours.",
            is_active=True,
        )
        self.db.add(plan)
        self.db.flush()

        topics = self.db.query(Topic).filter(Topic.user_id == user.id).all()
        # Score topics similarly to recommendation engine
        scored = []
        for t in topics:
            score = (100 - t.knowledge_level) + (t.importance * 10)
            if t.quiz_average is not None:
                score += max(0, 60 - t.quiz_average)
            scored.append((score, t))
        scored.sort(key=lambda x: x[0], reverse=True)

        for day_offset in range(data.days):
            day = start + timedelta(days=day_offset)
            remaining = minutes_budget
            cursor_minutes = base_start.hour * 60 + base_start.minute
            day_topics = scored[day_offset % max(len(scored), 1) :] + scored[: day_offset % max(len(scored), 1)]
            if not day_topics:
                continue
            for score, topic in day_topics:
                if remaining < 20:
                    break
                block = 45 if topic.knowledge_level < 55 else 30
                block = min(block, remaining)
                st = time(cursor_minutes // 60 % 24, cursor_minutes % 60)
                cursor_minutes += block + 10
                et = time(cursor_minutes // 60 % 24, cursor_minutes % 60)
                activity = "revision" if topic.knowledge_level < 70 else "study"
                self.db.add(
                    StudySession(
                        user_id=user.id,
                        plan_id=plan.id,
                        subject_id=topic.subject_id,
                        topic_id=topic.id,
                        title=f"{topic.name} {'Revision' if activity == 'revision' else 'Study'}",
                        scheduled_date=day,
                        start_time=st,
                        end_time=et,
                        duration_minutes=block,
                        status=SessionStatus.planned,
                        activity_type=activity,
                    )
                )
                remaining -= block
                # Add short quiz/flashcard slot for weak topics
                if topic.knowledge_level < 60 and remaining >= 20:
                    qblock = 20
                    st = time(cursor_minutes // 60 % 24, cursor_minutes % 60)
                    cursor_minutes += qblock + 5
                    et = time(cursor_minutes // 60 % 24, cursor_minutes % 60)
                    self.db.add(
                        StudySession(
                            user_id=user.id,
                            plan_id=plan.id,
                            subject_id=topic.subject_id,
                            topic_id=topic.id,
                            title=f"{topic.name} Practice Quiz",
                            scheduled_date=day,
                            start_time=st,
                            end_time=et,
                            duration_minutes=qblock,
                            status=SessionStatus.planned,
                            activity_type="quiz",
                        )
                    )
                    remaining -= qblock

        self.db.commit()
        self.db.refresh(plan)
        return plan

    def adapt_after_miss(self, user: User, session_id: str) -> StudyPlan:
        session = (
            self.db.query(StudySession)
            .filter(StudySession.id == session_id, StudySession.user_id == user.id)
            .first()
        )
        if not session:
            raise AppError("Session not found", status_code=404)
        session.status = SessionStatus.missed
        # Reschedule only this session to tomorrow without touching completed work
        tomorrow = date.today() + timedelta(days=1)
        self.db.add(
            StudySession(
                user_id=user.id,
                plan_id=session.plan_id,
                subject_id=session.subject_id,
                topic_id=session.topic_id,
                title=session.title + " (rescheduled)",
                scheduled_date=tomorrow,
                start_time=session.start_time,
                end_time=session.end_time,
                duration_minutes=min(session.duration_minutes + 15, 90),
                status=SessionStatus.planned,
                activity_type=session.activity_type,
                notes="Rescheduled after missed session",
            )
        )
        self.db.commit()
        plan = self.db.get(StudyPlan, session.plan_id) if session.plan_id else None
        if not plan:
            raise AppError("No active plan", status_code=404)
        return plan

    def complete_session(self, user: User, session_id: str) -> StudySession:
        session = (
            self.db.query(StudySession)
            .filter(StudySession.id == session_id, StudySession.user_id == user.id)
            .first()
        )
        if not session:
            raise AppError("Session not found", status_code=404)
        session.status = SessionStatus.completed
        if session.topic_id:
            topic = self.db.get(Topic, session.topic_id)
            if topic and topic.user_id == user.id:
                topic.last_studied_at = datetime.now(timezone.utc)
                topic.revision_count += 1 if session.activity_type == "revision" else 0
                topic.knowledge_level = min(100.0, topic.knowledge_level + 3)
                if topic.knowledge_level > 0:
                    topic.status = TopicStatus.in_progress
        activity = StudyActivity(
            user_id=user.id,
            activity_date=date.today(),
            minutes=session.duration_minutes,
            activity_type=session.activity_type,
            subject_id=session.subject_id,
            topic_id=session.topic_id,
        )
        self.db.add(activity)
        self.db.commit()
        self.db.refresh(session)
        return session

    def today_sessions(self, user: User) -> list[StudySession]:
        return (
            self.db.query(StudySession)
            .filter(StudySession.user_id == user.id, StudySession.scheduled_date == date.today())
            .order_by(StudySession.start_time.asc())
            .all()
        )


class QuizService:
    def __init__(self, db: Session):
        self.db = db
        self.ai = AIClient()

    def generate(self, user: User, data: QuizGenerateRequest) -> Quiz:
        topic = None
        topic_name = "General"
        subject_context = ""
        if data.topic_id:
            topic = self.db.query(Topic).filter(Topic.id == data.topic_id, Topic.user_id == user.id).first()
            if not topic:
                raise AppError("Topic not found", status_code=404)
            topic_name = topic.name
            # Adaptive: bias toward weak area
            if data.adaptive and topic.quiz_average is not None and topic.quiz_average < 60:
                data.number_of_questions = min(30, data.number_of_questions + 2)

        # Pull weak topics for adaptive mix
        weak = (
            self.db.query(Topic)
            .filter(Topic.user_id == user.id)
            .order_by(Topic.knowledge_level.asc())
            .limit(3)
            .all()
        )
        weak_names = [t.name for t in weak]

        types = ", ".join(t.value for t in data.question_types)
        prompt = (
            f"Generate {data.number_of_questions} academic quiz questions as JSON: "
            '{"questions":[{"type":"mcq|true_false|short_answer|conceptual","prompt":"...",'
            '"options":["A","B","C","D"]|null,"correct_answer":"...","explanation":"...","topic_tag":"..."}]}'
            f"\nPrimary topic: {topic_name}\nDifficulty: {data.difficulty.value}\nTypes: {types}\n"
            f"Emphasize weak areas if relevant: {', '.join(weak_names)}"
        )

        questions_data = []
        try:
            result = self.ai.chat_json(
                [
                    {"role": "system", "content": "You are an exam question writer. Return valid JSON only."},
                    {"role": "user", "content": prompt},
                ]
            )
            questions_data = result.get("questions", [])
        except AppError:
            # Deterministic fallback questions so demos work offline
            questions_data = [
                {
                    "type": "mcq",
                    "prompt": f"Which statement best describes {topic_name}?",
                    "options": [
                        f"Core concept related to {topic_name}",
                        "Unrelated historical fact",
                        "Random definition",
                        "None of the above",
                    ],
                    "correct_answer": f"Core concept related to {topic_name}",
                    "explanation": "Fallback question generated without AI API.",
                    "topic_tag": topic_name,
                }
                for _ in range(data.number_of_questions)
            ]

        quiz = Quiz(
            user_id=user.id,
            subject_id=data.subject_id or (topic.subject_id if topic else None),
            unit_id=data.unit_id,
            topic_id=data.topic_id,
            title=f"Quiz: {topic_name}",
            difficulty=data.difficulty,
            question_count=len(questions_data),
        )
        self.db.add(quiz)
        self.db.flush()
        for i, q in enumerate(questions_data):
            qtype = q.get("type", "mcq")
            try:
                qt = QuestionType(qtype)
            except ValueError:
                qt = QuestionType.mcq
            self.db.add(
                QuizQuestion(
                    quiz_id=quiz.id,
                    question_type=qt,
                    prompt=q.get("prompt", "Question"),
                    options_json=json.dumps(q.get("options")) if q.get("options") else None,
                    correct_answer=str(q.get("correct_answer", "")),
                    explanation=q.get("explanation"),
                    topic_tag=q.get("topic_tag", topic_name),
                    order_index=i,
                )
            )
        self.db.commit()
        self.db.refresh(quiz)
        return quiz

    def submit(self, user: User, quiz_id: str, answers: list[dict]) -> QuizAttempt:
        quiz = self.db.query(Quiz).filter(Quiz.id == quiz_id, Quiz.user_id == user.id).first()
        if not quiz:
            raise AppError("Quiz not found", status_code=404)
        questions = {q.id: q for q in quiz.questions}
        score = 0
        topic_stats: dict[str, list[bool]] = {}
        attempt = QuizAttempt(
            quiz_id=quiz.id,
            user_id=user.id,
            max_score=float(len(questions)),
            completed_at=datetime.now(timezone.utc),
        )
        self.db.add(attempt)
        self.db.flush()

        for ans in answers:
            qid = ans["question_id"]
            q = questions.get(qid)
            if not q:
                continue
            correct = ans["user_answer"].strip().lower() == q.correct_answer.strip().lower()
            if correct:
                score += 1
            tag = q.topic_tag or "General"
            topic_stats.setdefault(tag, []).append(correct)
            self.db.add(
                QuizAnswer(
                    attempt_id=attempt.id,
                    question_id=q.id,
                    user_answer=ans["user_answer"],
                    is_correct=correct,
                )
            )

        attempt.score = float(score)
        attempt.percentage = round(100.0 * score / max(len(questions), 1), 1)
        strong = [t for t, r in topic_stats.items() if sum(r) / len(r) >= 0.7]
        weak = [t for t, r in topic_stats.items() if sum(r) / len(r) < 0.6]
        attempt.strong_topics_json = json.dumps(strong)
        attempt.weak_topics_json = json.dumps(weak)

        # Update topic knowledge
        if quiz.topic_id:
            topic = self.db.get(Topic, quiz.topic_id)
            if topic and topic.user_id == user.id:
                prev = topic.quiz_average
                topic.quiz_average = (
                    attempt.percentage
                    if prev is None
                    else round((prev * 0.4 + attempt.percentage * 0.6), 1)
                )
                # Blend knowledge toward quiz performance
                topic.knowledge_level = round(topic.knowledge_level * 0.5 + topic.quiz_average * 0.5, 1)
                topic.last_studied_at = datetime.now(timezone.utc)

        self.db.add(
            StudyActivity(
                user_id=user.id,
                activity_date=date.today(),
                minutes=15,
                activity_type="quiz",
                subject_id=quiz.subject_id,
                topic_id=quiz.topic_id,
            )
        )
        self.db.commit()
        self.db.refresh(attempt)
        return attempt


class FlashcardService:
    def __init__(self, db: Session):
        self.db = db
        self.ai = AIClient()

    def generate(self, user: User, data: FlashcardGenerateRequest) -> list[Flashcard]:
        topic_name = "Study topic"
        subject_id = data.subject_id
        topic_id = data.topic_id
        if topic_id:
            topic = self.db.query(Topic).filter(Topic.id == topic_id, Topic.user_id == user.id).first()
            if topic:
                topic_name = topic.name
                subject_id = topic.subject_id

        context = ""
        if data.document_id:
            chunks = (
                self.db.query(DocumentChunk)
                .filter(DocumentChunk.document_id == data.document_id, DocumentChunk.user_id == user.id)
                .limit(8)
                .all()
            )
            context = "\n".join(c.content for c in chunks)

        prompt = (
            f'Return JSON {{"cards":[{{"question":"...","answer":"...","difficulty":"easy|medium|hard"}}]}} '
            f"with {data.count} flashcards about {topic_name}."
        )
        if context:
            prompt += f"\nUse this source material:\n{context[:4000]}"

        cards_data = []
        try:
            result = self.ai.chat_json(
                [
                    {"role": "system", "content": "Create concise study flashcards. JSON only."},
                    {"role": "user", "content": prompt},
                ]
            )
            cards_data = result.get("cards", [])
        except AppError:
            cards_data = [
                {
                    "question": f"What is a key idea in {topic_name}?",
                    "answer": f"A foundational concept of {topic_name} (offline fallback card).",
                    "difficulty": "medium",
                }
                for _ in range(data.count)
            ]

        created = []
        for c in cards_data:
            try:
                diff = Difficulty(c.get("difficulty", "medium"))
            except ValueError:
                diff = Difficulty.medium
            card = Flashcard(
                user_id=user.id,
                subject_id=subject_id,
                topic_id=topic_id,
                question=c.get("question", "Q"),
                answer=c.get("answer", "A"),
                difficulty=diff,
                next_review_at=datetime.now(timezone.utc),
            )
            self.db.add(card)
            created.append(card)
        self.db.commit()
        for c in created:
            self.db.refresh(c)
        return created

    def review(self, user: User, card_id: str, rating: str) -> Flashcard:
        """Simple SM-2 inspired spaced repetition."""
        card = self.db.query(Flashcard).filter(Flashcard.id == card_id, Flashcard.user_id == user.id).first()
        if not card:
            raise AppError("Flashcard not found", status_code=404)
        q = {"hard": 2, "medium": 3, "easy": 4}.get(rating, 3)
        if q < 3:
            card.repetitions = 0
            card.interval_days = 1
        else:
            if card.repetitions == 0:
                card.interval_days = 1
            elif card.repetitions == 1:
                card.interval_days = 3
            else:
                card.interval_days = max(1, int(card.interval_days * card.ease_factor))
            card.repetitions += 1
            card.ease_factor = max(1.3, card.ease_factor + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)))
        card.review_status = rating
        card.last_reviewed_at = datetime.now(timezone.utc)
        card.next_review_at = datetime.now(timezone.utc) + timedelta(days=card.interval_days)
        self.db.commit()
        self.db.refresh(card)
        return card
