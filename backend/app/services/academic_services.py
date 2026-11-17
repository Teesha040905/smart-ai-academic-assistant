from __future__ import annotations

import json
import re
from datetime import date, datetime, time, timedelta, timezone
from typing import Optional
from uuid import uuid4

from fastapi import BackgroundTasks, UploadFile
from pymongo.database import Database

from app.ai.client import AIClient
from app.core.config import get_settings
from app.core import file_storage
from app.core.errors import AppError
from app.core.logging import get_logger
from app.models import (
    Difficulty,
    DocumentStatus,
    QuestionType,
    SessionStatus,
    TopicStatus,
    make_chunk,
    make_conversation,
    make_document,
    make_flashcard,
    make_message,
    make_quiz,
    make_quiz_answer,
    make_quiz_attempt,
    make_quiz_question,
    make_study_activity,
    make_study_plan,
    make_study_session,
)
from app.models.doc import Doc
from app.rag.pipeline import RAGService, chunk_text, clean_text, extract_text
from app.repositories import mongo as repo
from app.schemas import (
    ChatMessageCreate,
    FlashcardGenerateRequest,
    QuizGenerateRequest,
    StudyPlanGenerateRequest,
)

logger = get_logger(__name__)
settings = get_settings()


class DocumentService:
    def __init__(self, db: Database):
        self.db = db

    def list(self, user: Doc, q: Optional[str] = None, subject_id: Optional[str] = None) -> list[Doc]:
        query: dict = {"user_id": user.id}
        if subject_id:
            query["subject_id"] = subject_id
        docs = repo.find_many(self.db, "documents", query, sort=[("created_at", -1)])
        if q:
            like = q.lower()
            docs = [d for d in docs if like in (d.title or "").lower() or like in (d.original_filename or "").lower()]
        return docs

    def get_owned(self, user: Doc, document_id: str) -> Doc:
        doc = repo.find_one(self.db, "documents", {"id": document_id, "user_id": user.id})
        if not doc:
            raise AppError("Document not found", status_code=404)
        return doc

    async def upload(
        self,
        user: Doc,
        file: UploadFile,
        *,
        title: Optional[str] = None,
        subject_id: Optional[str] = None,
        unit_id: Optional[str] = None,
        topic_id: Optional[str] = None,
        background: Optional[BackgroundTasks] = None,
    ) -> Doc:
        filename = file.filename or "upload.bin"
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in settings.allowed_extension_set:
            raise AppError("File type not allowed", status_code=400, code="invalid_file")
        content = await file.read()
        max_bytes = settings.max_upload_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise AppError(f"File exceeds {settings.max_upload_mb}MB limit", status_code=400)
        mime = file.content_type or "application/octet-stream"
        stored = file_storage.save(user.id, ext, content, filename=filename, mime_type=mime)

        doc = make_document(
            user_id=user.id,
            subject_id=subject_id,
            unit_id=unit_id,
            topic_id=topic_id,
            title=title or filename,
            original_filename=filename,
            stored_filename=stored,
            mime_type=mime,
            file_size=len(content),
            status=DocumentStatus.pending,
            progress=0,
        )
        repo.insert(self.db, "documents", doc)

        if background:
            background.add_task(process_document_job, doc.id)
        else:
            process_document_job(doc.id)
        return doc

    def delete(self, user: Doc, document_id: str) -> None:
        doc = self.get_owned(user, document_id)
        RAGService().store.delete_document(doc.id, user.id)
        file_storage.delete(doc.stored_filename)
        repo.delete_many(self.db, "document_chunks", {"document_id": doc.id})
        repo.delete_one(self.db, "documents", {"id": doc.id})

    def file_bytes(self, doc: Doc) -> Optional[bytes]:
        return file_storage.read_bytes(doc.stored_filename)


def process_document_job(document_id: str) -> None:
    from app.core.database import get_database

    db = get_database()
    try:
        doc = repo.find_one(db, "documents", {"id": document_id})
        if not doc:
            return
        doc.status = DocumentStatus.processing
        doc.progress = 10
        repo.save(db, "documents", doc)

        ext = doc.original_filename.rsplit(".", 1)[-1] if "." in (doc.original_filename or "") else ""
        with file_storage.local_copy(doc.stored_filename, ext) as path:
            raw, page_count = extract_text(path, doc.mime_type)
        text = clean_text(raw)
        doc.page_count = page_count
        doc.progress = 40
        repo.save(db, "documents", doc)

        chunks = chunk_text(text)
        if not chunks:
            doc.status = DocumentStatus.failed
            doc.error_message = "No extractable text found"
            repo.save(db, "documents", doc)
            return

        ai = AIClient()
        rag = RAGService()
        rag.store.delete_document(doc.id, doc.user_id)
        repo.delete_many(db, "document_chunks", {"document_id": doc.id})

        contents = [c["content"] for c in chunks]
        embeddings: list[list[float]] = []
        batch = 32
        for i in range(0, len(contents), batch):
            embeddings.extend(ai.embed(contents[i : i + batch]))
            doc.progress = 40 + int(50 * (i + batch) / max(len(contents), 1))
            repo.save(db, "documents", doc)

        ids = []
        metadatas = []
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
            chunk_doc = make_chunk(
                id=chunk_id,
                document_id=doc.id,
                user_id=doc.user_id,
                chunk_index=c["chunk_index"],
                page_number=c["page_number"],
                content=c["content"],
                vector_id=chunk_id,
                token_estimate=c["token_estimate"],
            )
            # preserve provided id
            chunk_doc.id = chunk_id
            repo.insert(db, "document_chunks", chunk_doc)

        rag.store.upsert_chunks(ids=ids, embeddings=embeddings, documents=contents, metadatas=metadatas)
        doc.status = DocumentStatus.ready
        doc.progress = 100
        doc.error_message = None
        repo.save(db, "documents", doc)
        logger.info("document_processed document_id=%s chunks=%s", doc.id, len(chunks))
    except Exception as exc:
        logger.exception("document_processing_failed document_id=%s", document_id)
        doc = repo.find_one(db, "documents", {"id": document_id})
        if doc:
            doc.status = DocumentStatus.failed
            doc.error_message = str(exc)[:500]
            repo.save(db, "documents", doc)


class ChatService:
    def __init__(self, db: Database):
        self.db = db
        self.ai = AIClient()
        self.rag = RAGService()

    def list_conversations(self, user: Doc) -> list[Doc]:
        return repo.find_many(
            self.db, "conversations", {"user_id": user.id}, sort=[("updated_at", -1)]
        )

    def get_conversation(self, user: Doc, conversation_id: str) -> Doc:
        conv = repo.find_one(self.db, "conversations", {"id": conversation_id, "user_id": user.id})
        if not conv:
            raise AppError("Conversation not found", status_code=404)
        conv.messages = repo.find_many(
            self.db, "messages", {"conversation_id": conv.id}, sort=[("created_at", 1)]
        )
        return conv

    def create_conversation(
        self, user: Doc, title: str = "New conversation", subject_id: Optional[str] = None
    ) -> Doc:
        conv = make_conversation(user_id=user.id, title=title, subject_id=subject_id)
        repo.insert(self.db, "conversations", conv)
        return conv

    def delete_conversation(self, user: Doc, conversation_id: str) -> None:
        conv = self.get_conversation(user, conversation_id)
        repo.delete_many(self.db, "messages", {"conversation_id": conv.id})
        repo.delete_one(self.db, "conversations", {"id": conv.id})

    def export_conversation_pdf(self, user: Doc, conversation_id: str) -> bytes:
        from app.services.pdf_service import build_conversation_pdf

        conv = self.get_conversation(user, conversation_id)
        subject_name = None
        if conv.subject_id:
            sub = repo.find_one(self.db, "subjects", {"id": conv.subject_id})
            if sub:
                subject_name = sub.name

        return build_conversation_pdf(
            title=conv.title or "Study Session",
            subject_name=subject_name,
            messages=conv.messages,
        )

    def send_message(self, user: Doc, conversation_id: str, data: ChatMessageCreate) -> Doc:
        conv = self.get_conversation(user, conversation_id)
        user_msg = make_message(
            conversation_id=conv.id, user_id=user.id, role="user", content=data.content
        )
        repo.insert(self.db, "messages", user_msg)

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
        history = repo.find_many(
            self.db, "messages", {"conversation_id": conv.id}, sort=[("created_at", 1)]
        )
        messages = [{"role": "system", "content": system}]
        for m in history[-12:]:
            messages.append({"role": m.role, "content": m.content})
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

        if conv.title in ("New conversation", "Study session"):
            try:
                title_prompt = [
                    {"role": "system", "content": "Summarize the user's input into a very short, catchy title (max 5 words). ONLY output the title text, no quotes or extra formatting."},
                    {"role": "user", "content": data.content}
                ]
                new_title = self.ai.chat(title_prompt).strip('"\'. \n')
                conv.title = new_title if new_title else data.content[:60]
            except Exception:
                conv.title = data.content[:60]
            repo.save(self.db, "conversations", conv)

        assistant = make_message(
            conversation_id=conv.id,
            user_id=user.id,
            role="assistant",
            content=answer,
            sources_json=json.dumps(sources) if sources else None,
            used_rag=bool(sources),
            from_general_knowledge=from_general,
        )
        repo.insert(self.db, "messages", assistant)
        return assistant


class StudyPlannerService:
    def __init__(self, db: Database):
        self.db = db

    def generate(self, user: Doc, data: StudyPlanGenerateRequest) -> Doc:
        profile = repo.find_one(self.db, "student_profiles", {"user_id": user.id})
        hours = data.hours_per_day or (profile.daily_study_hours if profile else 3.0)
        minutes_budget = int(hours * 60)
        prefer = profile.preferred_study_time if profile else "evening"
        start_map = {"morning": time(7, 0), "afternoon": time(14, 0), "evening": time(18, 0)}
        base_start = start_map.get((prefer or "evening").lower(), time(18, 0))

        topics = repo.find_many(self.db, "topics", {"user_id": user.id})
        if not topics:
            # Subjects without a topic breakdown still get study time, one block per subject
            topics = [
                Doc(
                    id=None,
                    subject_id=s.id,
                    name=s.name,
                    knowledge_level=50.0,
                    importance=1.0,
                    quiz_average=None,
                )
                for s in repo.find_many(self.db, "subjects", {"user_id": user.id})
            ]
        if not topics:
            raise AppError(
                "Add at least one subject before generating a study plan",
                status_code=400,
                code="no_subjects",
            )

        for p in repo.find_many(self.db, "study_plans", {"user_id": user.id, "is_active": True}):
            p.is_active = False
            repo.save(self.db, "study_plans", p)

        start = date.today()
        end = start + timedelta(days=data.days - 1)
        plan = make_study_plan(
            user_id=user.id,
            title="Adaptive Study Plan",
            start_date=start,
            end_date=end,
            notes="Generated from exam urgency, weak topics, and available hours.",
            is_active=True,
        )
        repo.insert(self.db, "study_plans", plan)

        scored = []
        for t in topics:
            score = (100 - t.knowledge_level) + (t.importance * 10)
            if t.quiz_average is not None:
                score += max(0, 60 - t.quiz_average)
            scored.append((score, t))
        scored.sort(key=lambda x: x[0], reverse=True)

        sessions = []
        for day_offset in range(data.days):
            day = start + timedelta(days=day_offset)
            remaining = minutes_budget
            cursor_minutes = base_start.hour * 60 + base_start.minute
            if not scored:
                continue
            day_topics = scored[day_offset % len(scored) :] + scored[: day_offset % len(scored)]
            for score, topic in day_topics:
                if remaining < 20:
                    break
                block = 45 if topic.knowledge_level < 55 else 30
                block = min(block, remaining)
                st = time(cursor_minutes // 60 % 24, cursor_minutes % 60)
                cursor_minutes += block + 10
                et = time(cursor_minutes // 60 % 24, cursor_minutes % 60)
                activity = "revision" if topic.knowledge_level < 70 else "study"
                session = make_study_session(
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
                repo.insert(self.db, "study_sessions", session)
                sessions.append(session)
                remaining -= block
                if topic.knowledge_level < 60 and remaining >= 20:
                    qblock = 20
                    st = time(cursor_minutes // 60 % 24, cursor_minutes % 60)
                    cursor_minutes += qblock + 5
                    et = time(cursor_minutes // 60 % 24, cursor_minutes % 60)
                    quiz_session = make_study_session(
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
                    repo.insert(self.db, "study_sessions", quiz_session)
                    sessions.append(quiz_session)
                    remaining -= qblock

        plan.sessions = sessions
        return plan

    def adapt_after_miss(self, user: Doc, session_id: str) -> Doc:
        session = repo.find_one(self.db, "study_sessions", {"id": session_id, "user_id": user.id})
        if not session:
            raise AppError("Session not found", status_code=404)
        session.status = SessionStatus.missed
        repo.save(self.db, "study_sessions", session)
        tomorrow = date.today() + timedelta(days=1)
        new_session = make_study_session(
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
        repo.insert(self.db, "study_sessions", new_session)
        if not session.plan_id:
            raise AppError("No active plan", status_code=404)
        plan = repo.find_one(self.db, "study_plans", {"id": session.plan_id})
        if not plan:
            raise AppError("No active plan", status_code=404)
        plan.sessions = repo.find_many(self.db, "study_sessions", {"plan_id": plan.id})
        return plan

    def complete_session(self, user: Doc, session_id: str) -> Doc:
        session = repo.find_one(self.db, "study_sessions", {"id": session_id, "user_id": user.id})
        if not session:
            raise AppError("Session not found", status_code=404)
        session.status = SessionStatus.completed
        repo.save(self.db, "study_sessions", session)
        if session.topic_id:
            topic = repo.find_one(self.db, "topics", {"id": session.topic_id, "user_id": user.id})
            if topic:
                topic.last_studied_at = datetime.now(timezone.utc)
                if session.activity_type == "revision":
                    topic.revision_count += 1
                topic.knowledge_level = min(100.0, topic.knowledge_level + 3)
                if topic.knowledge_level > 0:
                    topic.status = TopicStatus.in_progress
                repo.save(self.db, "topics", topic)
        activity = make_study_activity(
            user_id=user.id,
            activity_date=date.today(),
            minutes=session.duration_minutes,
            activity_type=session.activity_type,
            subject_id=session.subject_id,
            topic_id=session.topic_id,
        )
        repo.insert(self.db, "study_activities", activity)
        return session

    def today_sessions(self, user: Doc) -> list[Doc]:
        today = date.today()
        sessions = repo.find_many(self.db, "study_sessions", {"user_id": user.id})
        today_list = [s for s in sessions if s.scheduled_date == today]
        today_list.sort(key=lambda s: (s.start_time is None, s.start_time or time(0, 0)))
        return today_list


def _subject_scope(db: Database, user: Doc, subject_id: Optional[str]) -> tuple[Optional[Doc], str]:
    """Owned subject plus a prompt line describing it (name, code, description, topics)."""
    if not subject_id:
        return None, ""
    subject = repo.find_one(db, "subjects", {"id": subject_id, "user_id": user.id})
    if not subject:
        raise AppError("Subject not found", status_code=404)
    parts = [f"Subject: {subject.name}"]
    if getattr(subject, "code", None):
        parts.append(f"Course code: {subject.code}")
    if getattr(subject, "description", None):
        parts.append(f"Description: {subject.description}")
    topics = repo.find_many(db, "topics", {"user_id": user.id, "subject_id": subject.id})
    if topics:
        parts.append("Syllabus topics: " + ", ".join(t.name for t in topics))
    parts.append(f"All questions must be about {subject.name}, not general knowledge.")
    return subject, "\n".join(parts)


_OPTION_PREFIX = re.compile(r"^\s*\(?([a-z])[\).:\-]\s+", re.IGNORECASE)


def _normalize_answer(text: str) -> str:
    return _OPTION_PREFIX.sub("", text or "").strip().lower()


def _resolve_correct_option(correct: str, options: list[str]) -> str:
    """Map an AI-provided answer ("B", "B) Paris", "Paris") onto the matching option text."""
    key = (correct or "").strip()
    norm = _normalize_answer(key)
    for opt in options:
        if _normalize_answer(opt) == norm or opt.strip().lower() == key.lower():
            return opt
    if len(key.rstrip(").:")) == 1 and key[0].isalpha():
        idx = ord(key[0].lower()) - ord("a")
        if 0 <= idx < len(options):
            return options[idx]
        for opt in options:
            m = _OPTION_PREFIX.match(opt)
            if m and m.group(1).lower() == key[0].lower():
                return opt
    return key


class QuizService:
    def __init__(self, db: Database):
        self.db = db
        self.ai = AIClient()

    def generate(self, user: Doc, data: QuizGenerateRequest) -> Doc:
        topic = None
        topic_name = "General"
        subject, subject_context = _subject_scope(self.db, user, data.subject_id)
        if subject:
            topic_name = subject.name
        if data.topic_id:
            topic = repo.find_one(self.db, "topics", {"id": data.topic_id, "user_id": user.id})
            if not topic:
                raise AppError("Topic not found", status_code=404)
            topic_name = topic.name
            if data.adaptive and topic.quiz_average is not None and topic.quiz_average < 60:
                data.number_of_questions = min(30, data.number_of_questions + 2)

        weak_query = {"user_id": user.id}
        if subject:
            weak_query["subject_id"] = subject.id
        weak = repo.find_many(
            self.db, "topics", weak_query, sort=[("knowledge_level", 1)], limit=3
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
        if subject_context:
            prompt += f"\n{subject_context}"

        try:
            result = self.ai.chat_json(
                [
                    {"role": "system", "content": "You are an exam question writer. Return valid JSON only."},
                    {"role": "user", "content": prompt},
                ]
            )
            questions_data = result.get("questions", [])
        except AppError:
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

        quiz = make_quiz(
            user_id=user.id,
            subject_id=data.subject_id or (topic.subject_id if topic else None),
            unit_id=data.unit_id,
            topic_id=data.topic_id,
            title=f"Quiz: {topic_name}",
            difficulty=data.difficulty,
            question_count=len(questions_data),
        )
        repo.insert(self.db, "quizzes", quiz)
        questions = []
        for i, q in enumerate(questions_data):
            qtype = q.get("type", "mcq")
            try:
                qt = QuestionType(qtype)
            except ValueError:
                qt = QuestionType.mcq
            question = make_quiz_question(
                quiz_id=quiz.id,
                question_type=qt,
                prompt=q.get("prompt", "Question"),
                options_json=json.dumps(q.get("options")) if q.get("options") else None,
                correct_answer=str(q.get("correct_answer", "")),
                explanation=q.get("explanation"),
                topic_tag=q.get("topic_tag", topic_name),
                order_index=i,
            )
            repo.insert(self.db, "quiz_questions", question)
            questions.append(question)
        quiz.questions = questions
        return quiz

    def submit(self, user: Doc, quiz_id: str, answers: list[dict]) -> Doc:
        quiz = repo.find_one(self.db, "quizzes", {"id": quiz_id, "user_id": user.id})
        if not quiz:
            raise AppError("Quiz not found", status_code=404)
        questions = {
            q.id: q for q in repo.find_many(self.db, "quiz_questions", {"quiz_id": quiz.id})
        }
        score = 0
        topic_stats: dict[str, list[bool]] = {}
        attempt = make_quiz_attempt(
            quiz_id=quiz.id,
            user_id=user.id,
            max_score=float(len(questions)),
            completed_at=datetime.now(timezone.utc),
        )
        repo.insert(self.db, "quiz_attempts", attempt)

        review = []
        for ans in answers:
            qid = ans["question_id"]
            q = questions.get(qid)
            if not q:
                continue
            options = json.loads(q.options_json) if q.options_json else []
            correct_answer = _resolve_correct_option(q.correct_answer, [str(o) for o in options])
            user_answer = ans["user_answer"]
            correct = bool(user_answer.strip()) and (
                _normalize_answer(user_answer) == _normalize_answer(correct_answer)
            )
            review.append(
                {
                    "question_id": q.id,
                    "user_answer": user_answer,
                    "correct_answer": correct_answer,
                    "is_correct": correct,
                    "explanation": q.explanation,
                }
            )
            if correct:
                score += 1
            tag = q.topic_tag or "General"
            topic_stats.setdefault(tag, []).append(correct)
            answer = make_quiz_answer(
                attempt_id=attempt.id,
                question_id=q.id,
                user_answer=ans["user_answer"],
                is_correct=correct,
            )
            repo.insert(self.db, "quiz_answers", answer)

        attempt.score = float(score)
        attempt.percentage = round(100.0 * score / max(len(questions), 1), 1)
        strong = [t for t, r in topic_stats.items() if sum(r) / len(r) >= 0.7]
        weak = [t for t, r in topic_stats.items() if sum(r) / len(r) < 0.6]
        attempt.strong_topics_json = json.dumps(strong)
        attempt.weak_topics_json = json.dumps(weak)
        repo.save(self.db, "quiz_attempts", attempt)

        if quiz.topic_id:
            topic = repo.find_one(self.db, "topics", {"id": quiz.topic_id, "user_id": user.id})
            if topic:
                prev = topic.quiz_average
                topic.quiz_average = (
                    attempt.percentage
                    if prev is None
                    else round((prev * 0.4 + attempt.percentage * 0.6), 1)
                )
                topic.knowledge_level = round(topic.knowledge_level * 0.5 + topic.quiz_average * 0.5, 1)
                topic.last_studied_at = datetime.now(timezone.utc)
                repo.save(self.db, "topics", topic)

        activity = make_study_activity(
            user_id=user.id,
            activity_date=date.today(),
            minutes=15,
            activity_type="quiz",
            subject_id=quiz.subject_id,
            topic_id=quiz.topic_id,
        )
        repo.insert(self.db, "study_activities", activity)
        # per-question results for the response only (answers are stored in quiz_answers)
        attempt.review = review
        return attempt


class FlashcardService:
    def __init__(self, db: Database):
        self.db = db
        self.ai = AIClient()

    def generate(self, user: Doc, data: FlashcardGenerateRequest) -> list[Doc]:
        topic_name = "Study topic"
        subject_id = data.subject_id
        topic_id = data.topic_id
        subject, subject_context = _subject_scope(self.db, user, subject_id)
        if subject:
            topic_name = subject.name
        if topic_id:
            topic = repo.find_one(self.db, "topics", {"id": topic_id, "user_id": user.id})
            if topic:
                topic_name = topic.name
                subject_id = topic.subject_id

        context = ""
        if data.document_id:
            chunks = repo.find_many(
                self.db,
                "document_chunks",
                {"document_id": data.document_id, "user_id": user.id},
                limit=8,
            )
            context = "\n".join(c.content for c in chunks)

        prompt = (
            f'Return JSON {{"cards":[{{"question":"...","answer":"...","difficulty":"easy|medium|hard"}}]}} '
            f"with {data.count} flashcards about {topic_name}."
        )
        if subject_context:
            prompt += f"\n{subject_context}"
        if context:
            prompt += f"\nUse this source material:\n{context[:4000]}"

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
            card = make_flashcard(
                user_id=user.id,
                subject_id=subject_id,
                topic_id=topic_id,
                question=c.get("question", "Q"),
                answer=c.get("answer", "A"),
                difficulty=diff,
                next_review_at=datetime.now(timezone.utc),
            )
            repo.insert(self.db, "flashcards", card)
            created.append(card)
        return created

    def review(self, user: Doc, card_id: str, rating: str) -> Doc:
        card = repo.find_one(self.db, "flashcards", {"id": card_id, "user_id": user.id})
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
        repo.save(self.db, "flashcards", card)
        return card
