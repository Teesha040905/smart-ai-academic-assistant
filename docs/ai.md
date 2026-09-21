# AI & RAG

## Provider

OpenAI-compatible HTTP API via `AI_BASE_URL` + `AI_API_KEY`.

If no API key is set:

- Embeddings fall back to a local hashed bag-of-words vector (enough for demos).
- Quiz/flashcard/chat use deterministic offline fallbacks with clear messaging.

## RAG pipeline

```text
Upload → extract (PDF/DOCX/PPTX/TXT) → clean → chunk → embed → Chroma upsert
Question → embed → metadata-filtered similarity search (user_id) → context → LLM
```

Citations are taken only from retrieved chunk metadata (`document_title`, `page_number`). The tutor prompt forbids inventing page references.

When retrieval is empty/weak, the UI/API marks `from_general_knowledge`.

## Vector store decision

**ChromaDB** — simple local persistence + Docker image; metadata filters enforce user isolation. Swap point: `app/rag/pipeline.py` → `VectorStore`.

## Modular AI layout

```text
app/ai/client.py          LLM + embeddings
app/rag/pipeline.py       extract/chunk/retrieve
app/services/academic_services.py  chat, quiz, flashcards, planner, documents
app/services/recommendation_service.py  deterministic rules
```
