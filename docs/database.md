# Database schema

## Design principles

- Every academic row includes `user_id` and is filtered in services.
- Soft academic logic (knowledge %, readiness) lives in application code, not DB triggers.
- Document chunks are stored in PostgreSQL for audit; embeddings live in Chroma with matching metadata.

## Core entities

| Entity | Purpose |
|--------|---------|
| User / StudentProfile | Auth + personalization |
| Subject / Unit / Topic | Syllabus tree + knowledge levels |
| Document / DocumentChunk | Uploads + extracted text |
| Conversation / Message | AI Tutor history + citations |
| StudyPlan / StudySession | Planner + adaptive reschedule |
| Quiz / QuizQuestion / QuizAttempt / QuizAnswer | Assessment loop |
| Flashcard | Spaced repetition |
| Exam / Assignment | Deadlines driving urgency |
| Notification / Recommendation | Smart reminders |
| StudyActivity / PerformanceRecord | Analytics & streak |

## Progress calculation

- Topic knowledge: `0–100` updated from study sessions and quiz blends.
- Unit progress: average of topic knowledge (or manual override).
- Subject progress: average of all subject topics.
- Exam readiness: weighted blend — syllabus 35%, quizzes 30%, revision 20%, practice 15%.

## Migrations

Development uses `Base.metadata.create_all` on startup. For production, introduce Alembic migrations from this schema before changing columns.
