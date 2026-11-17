"""Text extraction, chunking, and Chroma vector store."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

from app.core.config import get_settings
from app.core.logging import get_logger
from app.ai.client import AIClient

logger = get_logger(__name__)


def _cosine_distance(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5 or 1.0
    nb = sum(x * x for x in b) ** 0.5 or 1.0
    return 1.0 - (dot / (na * nb))


class _InMemoryVectorCollection:
    """Fallback store when chromadb is not installed."""

    def __init__(self) -> None:
        self._rows: dict[str, dict[str, Any]] = {}

    def upsert(self, ids, embeddings, documents, metadatas):
        for i, _id in enumerate(ids):
            self._rows[_id] = {
                "embedding": embeddings[i],
                "document": documents[i],
                "metadata": metadatas[i],
            }

    def delete(self, where):
        def match(meta: dict) -> bool:
            if "$and" in where:
                return all(match(cond) for cond in where["$and"])
            return all(meta.get(k) == v for k, v in where.items())

        to_del = [i for i, row in self._rows.items() if match(row["metadata"])]
        for i in to_del:
            del self._rows[i]

    def query(self, query_embeddings, n_results=5, where=None, include=None):
        q = query_embeddings[0]

        def match(meta: dict) -> bool:
            if not where:
                return True
            if "$and" in where:
                return all(all(meta.get(k) == v for k, v in cond.items()) for cond in where["$and"])
            return all(meta.get(k) == v for k, v in where.items())

        scored = []
        for _id, row in self._rows.items():
            if not match(row["metadata"]):
                continue
            scored.append((_cosine_distance(q, row["embedding"]), _id, row))
        scored.sort(key=lambda x: x[0])
        top = scored[:n_results]
        return {
            "ids": [[t[1] for t in top]],
            "documents": [[t[2]["document"] for t in top]],
            "metadatas": [[t[2]["metadata"] for t in top]],
            "distances": [[t[0] for t in top]],
        }


class _MongoVectorCollection:
    """Durable vector store kept in MongoDB (``vector_chunks``); cosine ranking in Python.

    Fine for per-student document volumes and needs no extra service, so it suits free hosting.
    """

    _FILTER_KEYS = ("user_id", "document_id", "subject_id")

    def __init__(self) -> None:
        from app.core.database import get_database

        self._col = get_database()["vector_chunks"]

    def _mongo_filter(self, where: Optional[dict]) -> dict[str, Any]:
        if not where:
            return {}
        conds = where["$and"] if "$and" in where else [where]
        flt: dict[str, Any] = {}
        for cond in conds:
            for k, v in cond.items():
                flt[k if k in self._FILTER_KEYS else f"metadata.{k}"] = v
        return flt

    def upsert(self, ids, embeddings, documents, metadatas):
        from pymongo import ReplaceOne

        ops = []
        for i, _id in enumerate(ids):
            meta = metadatas[i]
            ops.append(
                ReplaceOne(
                    {"_id": _id},
                    {
                        "_id": _id,
                        "user_id": meta.get("user_id"),
                        "document_id": meta.get("document_id"),
                        "subject_id": meta.get("subject_id"),
                        "embedding": embeddings[i],
                        "document": documents[i],
                        "metadata": meta,
                    },
                    upsert=True,
                )
            )
        if ops:
            self._col.bulk_write(ops, ordered=False)

    def delete(self, where):
        self._col.delete_many(self._mongo_filter(where))

    def query(self, query_embeddings, n_results=5, where=None, include=None):
        q = query_embeddings[0]
        scored = []
        for row in self._col.find(self._mongo_filter(where), {"embedding": 1, "document": 1, "metadata": 1}):
            scored.append((_cosine_distance(q, row["embedding"]), row))
        scored.sort(key=lambda x: x[0])
        top = scored[:n_results]
        return {
            "ids": [[t[1]["_id"] for t in top]],
            "documents": [[t[1]["document"] for t in top]],
            "metadatas": [[t[1]["metadata"] for t in top]],
            "distances": [[t[0] for t in top]],
        }


def extract_text(path: Path, mime_type: str) -> tuple[str, Optional[int]]:
    suffix = path.suffix.lower()
    if suffix == ".pdf" or "pdf" in mime_type:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            pages.append(f"\n[[PAGE:{i+1}]]\n{text}")
        return "\n".join(pages), len(reader.pages)

    if suffix in {".docx"} or "word" in mime_type:
        from docx import Document as DocxDocument

        doc = DocxDocument(str(path))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip()), None

    if suffix in {".pptx", ".ppt"} or "presentation" in mime_type:
        from pptx import Presentation

        prs = Presentation(str(path))
        chunks = []
        for i, slide in enumerate(prs.slides, start=1):
            texts = []
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text:
                    texts.append(shape.text)
            chunks.append(f"\n[[PAGE:{i}]]\n" + "\n".join(texts))
        return "\n".join(chunks), len(prs.slides)

    if suffix == ".txt" or "text" in mime_type:
        return path.read_text(encoding="utf-8", errors="ignore"), None

    # Images: store placeholder note (OCR can be added later)
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        return f"[Image file: {path.name}. OCR not enabled; use text documents for RAG.]", 1

    raise ValueError(f"Unsupported file type: {suffix}")


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> list[dict[str, Any]]:
    """Split text into overlapping chunks, preserving page markers when present."""
    pages = re.split(r"\[\[PAGE:(\d+)\]\]", text)
    # pages like ['', '1', 'content', '2', 'content', ...]
    segments: list[tuple[Optional[int], str]] = []
    if len(pages) == 1:
        segments.append((None, pages[0]))
    else:
        i = 1
        while i < len(pages):
            try:
                page_no = int(pages[i])
            except ValueError:
                page_no = None
            content = pages[i + 1] if i + 1 < len(pages) else ""
            segments.append((page_no, content))
            i += 2

    chunks: list[dict[str, Any]] = []
    idx = 0
    for page_no, content in segments:
        content = content.strip()
        if not content:
            continue
        start = 0
        while start < len(content):
            end = min(len(content), start + chunk_size)
            piece = content[start:end].strip()
            if piece:
                chunks.append(
                    {
                        "chunk_index": idx,
                        "page_number": page_no,
                        "content": piece,
                        "token_estimate": max(1, len(piece.split())),
                    }
                )
                idx += 1
            if end >= len(content):
                break
            start = max(end - overlap, start + 1)
    return chunks


class VectorStore:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._client = None
        self._collection = None

    def _ensure(self):
        if self._collection is not None:
            return
        mode = (self.settings.vector_store or "auto").lower()
        if mode == "mongo":
            self._collection = _MongoVectorCollection()
            return
        if mode == "memory":
            self._collection = _InMemoryVectorCollection()
            return
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            try:
                self._client = chromadb.HttpClient(
                    host=self.settings.chroma_host,
                    port=self.settings.chroma_port,
                    settings=ChromaSettings(anonymized_telemetry=False),
                )
                self._collection = self._client.get_or_create_collection(
                    name=self.settings.chroma_collection,
                    metadata={"hnsw:space": "cosine"},
                )
                return
            except Exception as exc:
                logger.warning("chroma_http_unavailable using_persistent error=%s", str(exc))
                path = Path("./data/chroma")
                path.mkdir(parents=True, exist_ok=True)
                self._client = chromadb.PersistentClient(path=str(path))
                self._collection = self._client.get_or_create_collection(
                    name=self.settings.chroma_collection,
                    metadata={"hnsw:space": "cosine"},
                )
        except ImportError:
            if mode == "chroma":
                raise
            logger.info("chromadb_not_installed using_mongo_vector_store")
            self._collection = _MongoVectorCollection()

    def upsert_chunks(
        self,
        *,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        self._ensure()
        self._collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def delete_document(self, document_id: str, user_id: str) -> None:
        self._ensure()
        try:
            self._collection.delete(where={"$and": [{"document_id": document_id}, {"user_id": user_id}]})
        except Exception:
            # Fallback: some chroma versions need simpler where
            try:
                self._collection.delete(where={"document_id": document_id})
            except Exception as exc:
                logger.warning("chroma_delete_failed error=%s", str(exc))

    def query(
        self,
        *,
        user_id: str,
        query_embedding: list[float],
        n_results: int = 5,
        document_id: Optional[str] = None,
        subject_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        self._ensure()
        where: dict[str, Any] = {"user_id": user_id}
        if document_id:
            where = {"$and": [{"user_id": user_id}, {"document_id": document_id}]}
        elif subject_id:
            where = {"$and": [{"user_id": user_id}, {"subject_id": subject_id}]}

        result = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        hits = []
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        dists = result.get("distances", [[]])[0]
        ids = result.get("ids", [[]])[0]
        for i, doc in enumerate(docs):
            hits.append(
                {
                    "id": ids[i] if i < len(ids) else None,
                    "content": doc,
                    "metadata": metas[i] if i < len(metas) else {},
                    "distance": dists[i] if i < len(dists) else None,
                }
            )
        return hits


class RAGService:
    def __init__(self) -> None:
        self.ai = AIClient()
        self.store = VectorStore()

    def retrieve(
        self,
        *,
        user_id: str,
        query: str,
        document_id: Optional[str] = None,
        subject_id: Optional[str] = None,
        n_results: int = 5,
    ) -> list[dict[str, Any]]:
        embedding = self.ai.embed([query])[0]
        return self.store.query(
            user_id=user_id,
            query_embedding=embedding,
            n_results=n_results,
            document_id=document_id,
            subject_id=subject_id,
        )

    def build_context(self, hits: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]], bool]:
        if not hits:
            return "", [], False
        # Filter weak matches (cosine distance — lower is better for chroma cosine space)
        strong = [h for h in hits if h.get("distance") is None or h["distance"] < 0.55]
        use = strong or hits[:3]
        blocks = []
        sources = []
        for h in use:
            meta = h.get("metadata") or {}
            title = meta.get("document_title", "Document")
            page = meta.get("page_number")
            label = f"{title}" + (f" (page {page})" if page else "")
            blocks.append(f"[{label}]\n{h['content']}")
            sources.append(
                {
                    "document_id": meta.get("document_id"),
                    "title": title,
                    "page": page,
                    "chunk_id": meta.get("chunk_id"),
                }
            )
        return "\n\n---\n\n".join(blocks), sources, True
