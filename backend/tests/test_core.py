"""Pytest suite for auth, subjects, recommendations, and isolation."""

from __future__ import annotations

import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-secret-key-for-pytest"
os.environ["AI_API_KEY"] = ""
os.environ["UPLOAD_DIR"] = "./test_uploads"

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Clear settings cache if already loaded
from app.core.config import get_settings

get_settings.cache_clear()

from app.core import database as db_module
from app.main import create_app
from app.models.base import Base
from app.services.recommendation_service import days_until


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    get_settings.cache_clear()

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    db_module.engine = engine
    db_module.SessionLocal = TestingSession

    def _get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[db_module.get_db] = _get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
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
    # Set quiz_average via second patch — schema supports it through TopicUpdate
    # knowledge_level already set; update quiz via direct would need field — TopicUpdate has quiz? 
    # TopicUpdate doesn't include quiz_average — knowledge alone + exam should trigger rec
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
