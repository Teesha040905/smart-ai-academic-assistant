"""Pytest suite against MongoDB test database."""

from __future__ import annotations

import os

os.environ["MONGODB_URL"] = "mongodb://localhost:27017"
os.environ["MONGODB_DB"] = "smart_academic_test"
os.environ["JWT_SECRET"] = "test-secret-key-for-pytest"
os.environ["AI_API_KEY"] = ""
os.environ["UPLOAD_DIR"] = "./test_uploads"

from datetime import date, timedelta
from contextlib import asynccontextmanager

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings

get_settings.cache_clear()

from app.core import database as db_module
from app.core.database import close_client, ensure_indexes, get_client
from app.main import create_app
from app.services.recommendation_service import days_until


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("MONGODB_DB", "smart_academic_test")
    get_settings.cache_clear()
    close_client()
    db_module._client = None

    client_mongo = get_client()
    client_mongo.drop_database("smart_academic_test")
    ensure_indexes(client_mongo["smart_academic_test"])

    app = create_app()

    @asynccontextmanager
    async def _lifespan(_: object):
        ensure_indexes(get_client()["smart_academic_test"])
        yield

    app.router.lifespan_context = _lifespan
    with TestClient(app) as c:
        yield c

    try:
        get_client().drop_database("smart_academic_test")
    except Exception:
        pass
    close_client()
    get_settings.cache_clear()


def _register(client, email="a@test.com", password="Password123!", name="Alice"):
    r = client.post("/api/v1/auth/register", json={"email": email, "password": password, "full_name": name})
    assert r.status_code == 200, r.text
    return r.json()


def _login(client, email="a@test.com", password="Password123!"):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_register_and_login(client):
    user = _register(client)
    assert user["email"] == "a@test.com"
    token = _login(client)
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["full_name"] == "Alice"


def test_invalid_login(client):
    _register(client)
    r = client.post("/api/v1/auth/login", json={"email": "a@test.com", "password": "wrong"})
    assert r.status_code == 401


def test_protected_route(client):
    r = client.get("/api/v1/subjects")
    assert r.status_code == 401


def test_subject_crud_and_progress(client):
    _register(client)
    token = _login(client)
    h = {"Authorization": f"Bearer {token}"}
    r = client.post("/api/v1/subjects", json={"name": "Machine Learning", "code": "ML"}, headers=h)
    assert r.status_code == 200
    sid = r.json()["id"]
    client.post(f"/api/v1/subjects/{sid}/units", json={"name": "Unit 1", "order_index": 1}, headers=h)
    t = client.post(
        f"/api/v1/subjects/{sid}/topics",
        json={"name": "CNN", "difficulty": "medium"},
        headers=h,
    )
    tid = t.json()["id"]
    client.patch(f"/api/v1/topics/{tid}", json={"knowledge_level": 85}, headers=h)
    s = client.get(f"/api/v1/subjects/{sid}", headers=h).json()
    assert s["progress"] == 85.0


def test_cross_user_isolation(client):
    _register(client, email="one@test.com", name="One")
    t1 = _login(client, "one@test.com")
    h1 = {"Authorization": f"Bearer {t1}"}
    sid = client.post("/api/v1/subjects", json={"name": "Private"}, headers=h1).json()["id"]

    _register(client, email="two@test.com", name="Two")
    t2 = _login(client, "two@test.com")
    h2 = {"Authorization": f"Bearer {t2}"}
    r = client.get(f"/api/v1/subjects/{sid}", headers=h2)
    assert r.status_code == 404


def test_recommendation_weak_topic_and_exam_urgency(client):
    _register(client)
    token = _login(client)
    h = {"Authorization": f"Bearer {token}"}
    sid = client.post("/api/v1/subjects", json={"name": "ML"}, headers=h).json()["id"]
    tid = client.post(
        f"/api/v1/subjects/{sid}/topics",
        json={"name": "Backpropagation", "difficulty": "hard"},
        headers=h,
    ).json()["id"]
    client.patch(f"/api/v1/topics/{tid}", json={"knowledge_level": 44}, headers=h)
    client.post(
        "/api/v1/exams",
        json={
            "subject_id": sid,
            "name": "ML Exam",
            "exam_date": (date.today() + timedelta(days=6)).isoformat(),
            "priority": "high",
        },
        headers=h,
    )
    recs = client.get("/api/v1/recommendations?refresh=true", headers=h).json()
    assert len(recs) >= 1
    assert any("Backpropagation" in r["title"] for r in recs)


def test_quiz_fallback_without_ai(client):
    _register(client)
    token = _login(client)
    h = {"Authorization": f"Bearer {token}"}
    sid = client.post("/api/v1/subjects", json={"name": "ML"}, headers=h).json()["id"]
    tid = client.post(f"/api/v1/subjects/{sid}/topics", json={"name": "CNN"}, headers=h).json()["id"]
    quiz = client.post(
        "/api/v1/ai/quiz",
        json={"topic_id": tid, "subject_id": sid, "number_of_questions": 3, "difficulty": "medium"},
        headers=h,
    )
    assert quiz.status_code == 200
    body = quiz.json()
    assert body["question_count"] == 3
    answers = [{"question_id": q["id"], "user_answer": "x"} for q in body["questions"]]
    attempt = client.post(f"/api/v1/quizzes/{body['id']}/submit", json={"answers": answers}, headers=h)
    assert attempt.status_code == 200
    assert "percentage" in attempt.json()


def test_days_until():
    assert days_until(date.today() + timedelta(days=6)) == 6


def test_invalid_document_extension(client):
    _register(client)
    token = _login(client)
    h = {"Authorization": f"Bearer {token}"}
    files = {"file": ("malware.exe", b"abc", "application/octet-stream")}
    r = client.post("/api/v1/documents", files=files, headers=h)
    assert r.status_code == 400


def test_plan_without_topics_uses_subjects(client):
    _register(client)
    h = {"Authorization": f"Bearer {_login(client)}"}
    client.post("/api/v1/subjects", json={"name": "Physics"}, headers=h)
    r = client.post("/api/v1/study-plans/generate", json={"days": 7}, headers=h)
    assert r.status_code == 200, r.text
    sessions = r.json()["sessions"]
    assert sessions
    assert {s["scheduled_date"] for s in sessions} == {
        (date.today() + timedelta(days=i)).isoformat() for i in range(7)
    }
    assert sessions[0]["title"].startswith("Physics")


def test_plan_without_subjects_is_rejected(client):
    _register(client)
    h = {"Authorization": f"Bearer {_login(client)}"}
    r = client.post("/api/v1/study-plans/generate", json={"days": 7}, headers=h)
    assert r.status_code == 400
    assert "subject" in r.json()["detail"].lower()
    assert client.get("/api/v1/study-plans/active", headers=h).json() is None


def test_quiz_and_flashcards_use_selected_subject(client):
    _register(client)
    h = {"Authorization": f"Bearer {_login(client)}"}
    sid = client.post("/api/v1/subjects", json={"name": "Software Testing"}, headers=h).json()["id"]

    quiz = client.post("/api/v1/ai/quiz", json={"subject_id": sid, "number_of_questions": 2}, headers=h)
    assert quiz.status_code == 200, quiz.text
    assert quiz.json()["title"] == "Quiz: Software Testing"
    assert quiz.json()["subject_id"] == sid

    cards = client.post("/api/v1/ai/flashcards", json={"subject_id": sid, "count": 2}, headers=h)
    assert cards.status_code == 200, cards.text
    assert all(c["subject_id"] == sid for c in cards.json())


def test_quiz_rejects_other_users_subject(client):
    _register(client, email="one@test.com", name="One")
    h1 = {"Authorization": f"Bearer {_login(client, 'one@test.com')}"}
    sid = client.post("/api/v1/subjects", json={"name": "Private"}, headers=h1).json()["id"]
    _register(client, email="two@test.com", name="Two")
    h2 = {"Authorization": f"Bearer {_login(client, 'two@test.com')}"}
    r = client.post("/api/v1/ai/quiz", json={"subject_id": sid}, headers=h2)
    assert r.status_code == 404


def test_quiz_submit_returns_per_question_review(client):
    _register(client)
    h = {"Authorization": f"Bearer {_login(client)}"}
    quiz = client.post("/api/v1/ai/quiz", json={"number_of_questions": 2}, headers=h).json()
    q1, q2 = quiz["questions"][:2]
    r = client.post(
        f"/api/v1/quizzes/{quiz['id']}/submit",
        json={"answers": [
            {"question_id": q1["id"], "user_answer": "definitely not an option"},
            {"question_id": q2["id"], "user_answer": ""},
        ]},
        headers=h,
    )
    assert r.status_code == 200, r.text
    review = {item["question_id"]: item for item in r.json()["review"]}
    assert set(review) == {q1["id"], q2["id"]}
    assert review[q1["id"]]["is_correct"] is False
    assert review[q2["id"]]["is_correct"] is False
    assert review[q1["id"]]["correct_answer"]

    # answering with the revealed correct option scores it as right
    right = client.post(
        f"/api/v1/quizzes/{quiz['id']}/submit",
        json={"answers": [{"question_id": q1["id"], "user_answer": review[q1["id"]]["correct_answer"]}]},
        headers=h,
    ).json()
    assert right["review"][0]["is_correct"] is True
    assert right["score"] == 1


def test_recommendations_for_subjects_without_topics(client):
    _register(client)
    h = {"Authorization": f"Bearer {_login(client)}"}
    client.post("/api/v1/subjects", json={"name": "Physics"}, headers=h)
    with_topics = client.post("/api/v1/subjects", json={"name": "Chemistry"}, headers=h).json()["id"]
    client.post(f"/api/v1/subjects/{with_topics}/topics", json={"name": "Bonding"}, headers=h)

    recs = client.get("/api/v1/recommendations?refresh=true", headers=h).json()
    titles = [r["title"] for r in recs]
    assert "Practise Physics" in titles
    assert "Focus on Bonding" in titles
    assert "Practise Chemistry" not in titles  # covered by its topics instead
    physics = next(r for r in recs if r["title"] == "Practise Physics")
    assert "No quizzes taken yet" in physics["reason"]


def test_forgot_password_does_not_leak_reset_token(client):
    _register(client)
    r = client.post("/api/v1/auth/forgot-password", json={"email": "a@test.com"})
    assert r.status_code == 200
    assert "token" not in r.text.lower()


def test_exam_and_assignment_require_owned_subject(client):
    _register(client, email="one@test.com", name="One")
    h1 = {"Authorization": f"Bearer {_login(client, 'one@test.com')}"}
    foreign = client.post("/api/v1/subjects", json={"name": "Private"}, headers=h1).json()["id"]
    _register(client, email="two@test.com", name="Two")
    h2 = {"Authorization": f"Bearer {_login(client, 'two@test.com')}"}
    exam = {"subject_id": foreign, "name": "Final", "exam_date": str(date.today())}
    assert client.post("/api/v1/exams", json=exam, headers=h2).status_code == 404
    exam["subject_id"] = "missing"
    assert client.post("/api/v1/exams", json=exam, headers=h2).status_code == 404
    task = {"title": "Report", "subject_id": foreign, "deadline": "2030-01-01T10:00:00"}
    assert client.post("/api/v1/assignments", json=task, headers=h2).status_code == 404


def test_syllabus_input_validation(client):
    _register(client)
    h = {"Authorization": f"Bearer {_login(client)}"}
    sid = client.post("/api/v1/subjects", json={"name": "Physics"}, headers=h).json()["id"]
    assert client.post("/api/v1/subjects", json={"name": "physics"}, headers=h).status_code == 409
    assert client.patch(f"/api/v1/subjects/{sid}", json={"color": "red; x"}, headers=h).status_code == 422
    assert client.post(f"/api/v1/subjects/{sid}/units", json={"name": "  "}, headers=h).status_code == 422
    assert client.post(f"/api/v1/subjects/{sid}/topics", json={"name": ""}, headers=h).status_code == 422
    r = client.post(f"/api/v1/subjects/{sid}/topics", json={"name": "Optics", "importance": -1}, headers=h)
    assert r.status_code == 422
    r = client.post(f"/api/v1/subjects/{sid}/topics", json={"name": "  Optics  "}, headers=h)
    assert r.status_code == 200 and r.json()["name"] == "Optics"


def test_dashboard_streak_counts_today(client):
    _register(client)
    h = {"Authorization": f"Bearer {_login(client)}"}
    client.post("/api/v1/subjects", json={"name": "Physics"}, headers=h)
    session = client.post("/api/v1/study-plans/generate", json={"days": 1}, headers=h).json()["sessions"][0]
    client.post(f"/api/v1/study-sessions/{session['id']}/complete", headers=h)
    assert client.get("/api/v1/dashboard", headers=h).json()["streak"]["streak_days"] == 1


def test_fallback_embeddings_are_stable_across_processes():
    import subprocess
    import sys

    code = "from app.ai.client import AIClient; print(AIClient()._hash_embed('linked list node')[:64])"
    runs = {subprocess.run([sys.executable, "-c", code], capture_output=True, text=True).stdout for _ in range(2)}
    assert len(runs) == 1 and runs != {""}


def test_delete_account_removes_quiz_questions_and_answers(client):
    _register(client)
    h = {"Authorization": f"Bearer {_login(client)}"}
    quiz = client.post("/api/v1/ai/quiz", json={"number_of_questions": 2}, headers=h).json()
    client.post(
        f"/api/v1/quizzes/{quiz['id']}/submit",
        json={"answers": [{"question_id": q["id"], "user_answer": ""} for q in quiz["questions"]]},
        headers=h,
    )
    assert client.delete("/api/v1/users/me", headers=h).status_code == 200
    db = get_client()["smart_academic_test"]
    assert db.quiz_questions.count_documents({"quiz_id": quiz["id"]}) == 0
    assert db.quiz_answers.count_documents({}) == 0


def test_document_lifecycle_with_gridfs_and_mongo_vectors(client, monkeypatch):
    """Production storage mode (Render): files in GridFS, vectors in MongoDB."""
    monkeypatch.setenv("FILE_STORAGE", "gridfs")
    monkeypatch.setenv("VECTOR_STORE", "mongo")
    get_settings.cache_clear()
    from app.core import file_storage
    from app.rag.pipeline import RAGService

    _register(client)
    h = {"Authorization": f"Bearer {_login(client)}"}
    body = b"Photosynthesis converts light energy into chemical energy in plants.\n" * 5
    r = client.post("/api/v1/documents", files={"file": ("notes.txt", body, "text/plain")}, headers=h)
    assert r.status_code in (200, 201), r.text
    doc_id = r.json()["id"]

    doc = client.get(f"/api/v1/documents/{doc_id}", headers=h).json()
    assert doc["status"] == "ready", doc

    db = get_client()["smart_academic_test"]
    stored = db.documents.find_one({"id": doc_id})["stored_filename"]
    assert stored.startswith(file_storage.GRIDFS_PREFIX)
    assert db["uploads.files"].count_documents({}) == 1
    assert db.vector_chunks.count_documents({"document_id": doc_id}) >= 1

    user_id = db.documents.find_one({"id": doc_id})["user_id"]
    hits = RAGService().retrieve(user_id=user_id, query="photosynthesis light energy", document_id=doc_id)
    assert hits and "Photosynthesis" in hits[0]["content"]
    assert RAGService().retrieve(user_id="someone-else", query="photosynthesis") == []

    dl = client.get(f"/api/v1/documents/{doc_id}/download", headers=h)
    assert dl.status_code == 200 and dl.content == body
    assert "notes.txt" in dl.headers["content-disposition"]

    assert client.delete(f"/api/v1/documents/{doc_id}", headers=h).status_code in (200, 204)
    assert db["uploads.files"].count_documents({}) == 0
    assert db.vector_chunks.count_documents({"document_id": doc_id}) == 0

    # deleting the account removes files and vectors of documents it still owns
    r = client.post("/api/v1/documents", files={"file": ("more.txt", body, "text/plain")}, headers=h)
    assert r.status_code in (200, 201), r.text
    assert db["uploads.files"].count_documents({}) == 1
    assert client.delete("/api/v1/users/me", headers=h).status_code in (200, 204)
    assert db["uploads.files"].count_documents({}) == 0
    assert db["uploads.chunks"].count_documents({}) == 0
    assert db.vector_chunks.count_documents({}) == 0


def test_production_requires_strong_jwt_secret(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("JWT_SECRET", "change-me-to-a-long-random-secret")
    get_settings.cache_clear()
    try:
        with pytest.raises(RuntimeError):
            get_settings()
        monkeypatch.setenv("JWT_SECRET", "x" * 48)
        get_settings.cache_clear()
        assert get_settings().is_production
    finally:
        monkeypatch.undo()
        get_settings.cache_clear()
