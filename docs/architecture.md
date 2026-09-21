# Architecture — Smart AI Academic Assistant

## Goals

One continuous learning loop: academic data → study → quiz → performance → recommendations → adaptive plan → study again.

## High-level diagram

```text
┌─────────────┐     REST/JWT      ┌──────────────────┐
│  Next.js UI │ ◄───────────────► │  FastAPI Backend │
└─────────────┘                   └────────┬─────────┘
                                           │
                    ┌──────────────────────┼──────────────────────┐
                    ▼                      ▼                      ▼
             PostgreSQL              ChromaDB               AI Provider
          (users, subjects,       (embeddings +          (chat, embed,
           quizzes, plans)         metadata)              summarize)
                                           │
                                    Background Worker
                                  (PDF extract → chunk
                                   → embed → READY)
```

## Backend layers

```text
api/          HTTP routes, auth deps, validation
schemas/      Pydantic request/response models
services/     Business logic (CRUD + domain rules)
repositories/ SQLAlchemy data access
ai/           LLM clients, quiz/flashcard/planner helpers
rag/          Chunking, embeddings, retrieval, citations
workers/      Document processing jobs
core/         Config, security, logging, errors
```

## Frontend layers

```text
app/          App Router pages (dashboard, subjects, tutor, …)
components/   UI building blocks + feature widgets
hooks/        Auth, theme, API helpers
lib/          API client, utilities
types/        Shared TypeScript types
```

## Auth & roles

- JWT bearer tokens; passwords hashed with bcrypt.
- `User.role ∈ {student, faculty, admin}` — only student flows are fully implemented.
- Every academic row is scoped by `user_id`; repositories enforce ownership.

## Deterministic vs generative AI

| Concern | Approach |
|---------|----------|
| Weak topics, exam urgency, readiness score | Deterministic rules in `services/recommendations.py` |
| Natural-language explanation of a recommendation | Optional LLM enrichment |
| Tutor answers from uploads | RAG + LLM; cite chunks only if retrieved |
| Quiz / flashcard generation | LLM with structured JSON schema validation |

## Vector isolation

Chroma metadata always includes `user_id`. Queries filter by authenticated user so retrieval cannot cross accounts.

## Extension points

- Faculty/admin routes can reuse the same auth middleware.
- Mobile apps consume the same `/api/v1` REST surface.
- Swap Chroma for pgvector by replacing `rag/vector_store.py`.
