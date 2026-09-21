# API overview

Base URL: `/api/v1`

Auth: `Authorization: Bearer <jwt>`

Interactive docs: `http://localhost:8000/docs`

## Auth

| Method | Path | Notes |
|--------|------|-------|
| POST | `/auth/register` | Creates student + empty profile |
| POST | `/auth/login` | Returns JWT |
| GET | `/auth/me` | Current user + profile |
| POST | `/auth/forgot-password` | Returns `dev_reset_token` in development |
| POST | `/auth/reset-password` | Consumes reset token |
| POST | `/auth/logout` | Client should discard token |

## Academic

CRUD under `/subjects`, `/units`, `/topics`, `/exams`, `/assignments`, `/documents`.

## AI

| Method | Path |
|--------|------|
| POST | `/ai/conversations` |
| POST | `/ai/conversations/{id}/messages` | RAG tutor |
| POST | `/ai/summarize` |
| POST | `/ai/quiz` |
| POST | `/ai/flashcards` |
| POST | `/study-plans/generate` |

## Intelligence

| Method | Path |
|--------|------|
| GET | `/dashboard` |
| GET | `/performance` |
| GET | `/knowledge-map` |
| GET | `/recommendations?refresh=true` |
| GET | `/search?q=` |

Errors return `{ "detail": "...", "code": "..." }` without stack traces.
