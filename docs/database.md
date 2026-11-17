# Database — MongoDB

## Connection

Configured via environment variables:

```text
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=smart_academic
```

Driver: **PyMongo**. Collections mirror the previous relational entities (`users`, `subjects`, `topics`, …).

## Collections (main)

| Collection | Purpose |
|------------|---------|
| users / student_profiles | Auth + personalization |
| subjects / units / topics | Syllabus tree + knowledge levels |
| documents / document_chunks | Uploads + extracted text |
| conversations / messages | AI Tutor history + citations |
| study_plans / study_sessions | Planner + adaptive reschedule |
| quizzes / quiz_questions / quiz_attempts / quiz_answers | Assessment loop |
| flashcards | Spaced repetition |
| exams / assignments | Deadlines driving urgency |
| recommendations | Smart next steps |
| study_activities | Analytics & streak |
| password_reset_tokens | Forgot-password flow |

Every academic document includes `user_id` for isolation.

Embeddings still live in **ChromaDB** (or the in-memory fallback), keyed by the same `document_id` / `user_id` metadata.

## Indexes

Created on startup by `ensure_indexes()` (unique email, ownership indexes, date sorts).
