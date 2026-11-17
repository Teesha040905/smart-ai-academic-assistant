"""Seed demo student into MongoDB.

Run: python -m app.scripts.seed
Demo login: demo@student.edu / DemoPass123!
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
import json

from app.core.config import get_settings
from app.core.database import ensure_indexes, get_client, get_database
from app.core.security import hash_password
from app.models import (
    AssignmentStatus,
    Difficulty,
    Priority,
    QuestionType,
    SessionStatus,
    TopicStatus,
    UserRole,
    make_assignment,
    make_exam,
    make_flashcard,
    make_profile,
    make_quiz,
    make_quiz_attempt,
    make_quiz_question,
    make_study_activity,
    make_study_plan,
    make_study_session,
    make_subject,
    make_topic,
    make_unit,
    make_user,
)
from app.repositories import mongo as repo
from app.services.recommendation_service import RecommendationEngine


def seed() -> None:
    settings = get_settings()
    get_client().admin.command("ping")
    db = get_database()
    ensure_indexes(db)

    existing = repo.find_one(db, "users", {"email": "demo@student.edu"})
    if existing:
        print("Demo user already exists — refreshing recommendations only.")
        RecommendationEngine(db).generate(existing)
        print(f"OK (mongodb://…/{settings.mongodb_db})")
        return

    user = make_user(
        email="demo@student.edu",
        hashed_password=hash_password("DemoPass123!"),
        full_name="John Demo",
        role=UserRole.student,
        theme="system",
    )
    repo.insert(db, "users", user)

    profile = make_profile(
        user_id=user.id,
        course="B.Tech",
        branch="Computer Engineering",
        semester=6,
        academic_year="2025-26",
        preferred_study_time="evening",
        daily_study_hours=3.0,
        learning_preferences=json.dumps(["visual", "practice-first"]),
        academic_goals="Score above 85%",
        notification_prefs=json.dumps({"exam_reminders": True, "study_slots": True, "quiz_drops": True}),
    )
    repo.insert(db, "student_profiles", profile)

    subjects_spec = [
        ("Machine Learning", "ML", "#0f766e"),
        ("Artificial Intelligence", "AI", "#1d4ed8"),
        ("Software Project Management", "SPM", "#b45309"),
        ("Mobile Communication", "MC", "#7c3aed"),
    ]
    subjects = {}
    for name, code, color in subjects_spec:
        s = make_subject(
            user_id=user.id,
            name=name,
            code=code,
            color=color,
            priority=Priority.high if code == "ML" else Priority.medium,
            exam_date=date.today() + timedelta(days=6) if code == "ML" else None,
        )
        repo.insert(db, "subjects", s)
        subjects[code] = s

    ml = subjects["ML"]
    units = []
    for i, uname in enumerate(
        ["Regression & Classification", "Neural Networks", "CNN & Vision", "Sequence Models", "GANs & Generative"],
        start=1,
    ):
        u = make_unit(subject_id=ml.id, user_id=user.id, name=f"Unit {i}: {uname}", order_index=i)
        repo.insert(db, "units", u)
        units.append(u)

    topic_defs = [
        (units[0], "Linear Regression", 85, Difficulty.easy),
        (units[0], "Classification", 72, Difficulty.medium),
        (units[1], "Backpropagation", 44, Difficulty.hard),
        (units[1], "Gradient Descent", 58, Difficulty.medium),
        (units[2], "CNN", 85, Difficulty.medium),
        (units[2], "Pooling", 80, Difficulty.easy),
        (units[3], "RNN", 72, Difficulty.medium),
        (units[4], "GAN", 51, Difficulty.hard),
    ]
    topics = {}
    for unit, name, knowledge, diff in topic_defs:
        t = make_topic(
            user_id=user.id,
            subject_id=ml.id,
            unit_id=unit.id,
            name=name,
            description=f"Demo topic: {name}",
            difficulty=diff,
            status=TopicStatus.completed if knowledge >= 80 else TopicStatus.in_progress,
            knowledge_level=float(knowledge),
            quiz_average=float(knowledge),
            revision_count=3 if knowledge >= 80 else 1,
            last_studied_at=datetime.now(timezone.utc) - timedelta(days=2 if knowledge >= 70 else 5),
            importance=1.5 if knowledge < 60 else 1.0,
        )
        repo.insert(db, "topics", t)
        topics[name] = t

    for code, names in {
        "AI": [("Search Algorithms", 82), ("Knowledge Representation", 70)],
        "SPM": [("Unit 4 — Risk Management", 65), ("Agile Practices", 78)],
        "MC": [("Cellular Networks", 68), ("Modulation", 74)],
    }.items():
        s = subjects[code]
        for name, kl in names:
            repo.insert(
                db,
                "topics",
                make_topic(
                    user_id=user.id,
                    subject_id=s.id,
                    name=name,
                    knowledge_level=float(kl),
                    quiz_average=float(kl),
                    status=TopicStatus.in_progress,
                    difficulty=Difficulty.medium,
                ),
            )

    exam = make_exam(
        user_id=user.id,
        subject_id=ml.id,
        name="Machine Learning Midterm",
        exam_date=date.today() + timedelta(days=6),
        exam_time=time(10, 0),
        syllabus="Units 1–5 with emphasis on neural nets, CNN, GAN, backpropagation",
        priority=Priority.high,
    )
    repo.insert(db, "exams", exam)

    repo.insert(
        db,
        "assignments",
        make_assignment(
            user_id=user.id,
            subject_id=subjects["SPM"].id,
            title="SPM Case Study Report",
            description="Analyze risk management for a sample software project.",
            deadline=datetime.now(timezone.utc) + timedelta(days=4),
            priority=Priority.medium,
            status=AssignmentStatus.in_progress,
        ),
    )

    quiz = make_quiz(
        user_id=user.id,
        subject_id=ml.id,
        topic_id=topics["Backpropagation"].id,
        title="Backpropagation Practice",
        difficulty=Difficulty.medium,
        question_count=10,
    )
    repo.insert(db, "quizzes", quiz)
    for i in range(10):
        repo.insert(
            db,
            "quiz_questions",
            make_quiz_question(
                quiz_id=quiz.id,
                question_type=QuestionType.mcq,
                prompt=f"Backpropagation concept question {i+1}",
                options_json=json.dumps(["A", "B", "C", "D"]),
                correct_answer="A",
                topic_tag="Backpropagation",
                order_index=i,
            ),
        )
    for pct in (42, 48, 55):
        repo.insert(
            db,
            "quiz_attempts",
            make_quiz_attempt(
                quiz_id=quiz.id,
                user_id=user.id,
                score=pct / 10,
                max_score=10,
                percentage=float(pct),
                strong_topics_json=json.dumps(["CNN Architecture"]),
                weak_topics_json=json.dumps(["Backpropagation", "Gradient Descent"]),
                completed_at=datetime.now(timezone.utc) - timedelta(days=10 - pct // 10),
            ),
        )

    plan = make_study_plan(
        user_id=user.id,
        title="Adaptive Study Plan",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=6),
        is_active=True,
        notes="Seeded demo plan",
    )
    repo.insert(db, "study_plans", plan)

    today_blocks = [
        (time(9, 0), time(9, 45), topics["Backpropagation"], "Backpropagation Revision", "revision", 45),
        (time(11, 0), time(11, 45), None, "Mobile Communication", "study", 45),
        (time(16, 0), time(16, 30), topics["GAN"], "GAN Revision", "revision", 30),
        (time(18, 0), time(18, 20), topics["Backpropagation"], "Practice Quiz", "quiz", 20),
        (time(20, 0), time(20, 15), topics["CNN"], "Flashcards", "flashcards", 15),
    ]
    for st, et, topic, title, atype, mins in today_blocks:
        repo.insert(
            db,
            "study_sessions",
            make_study_session(
                user_id=user.id,
                plan_id=plan.id,
                subject_id=topic.subject_id if topic else subjects["MC"].id,
                topic_id=topic.id if topic else None,
                title=title,
                scheduled_date=date.today(),
                start_time=st,
                end_time=et,
                duration_minutes=mins,
                status=SessionStatus.planned,
                activity_type=atype,
            ),
        )

    for i in range(12):
        d = date.today() - timedelta(days=i)
        repo.insert(
            db,
            "study_activities",
            make_study_activity(
                user_id=user.id,
                activity_date=d,
                minutes=45 + (i % 3) * 15,
                activity_type="study",
                subject_id=ml.id,
            ),
        )

    for q, a in [
        ("What is backpropagation?", "An algorithm for computing gradients in neural networks."),
        ("What does a GAN consist of?", "A generator and a discriminator trained adversarially."),
        ("What is max pooling?", "Downsampling that keeps the strongest activation in a window."),
    ]:
        repo.insert(
            db,
            "flashcards",
            make_flashcard(
                user_id=user.id,
                subject_id=ml.id,
                topic_id=topics["Backpropagation"].id if "back" in q.lower() else topics["GAN"].id,
                question=q,
                answer=a,
                difficulty=Difficulty.medium,
            ),
        )

    RecommendationEngine(db).generate(user)
    print("Seeded demo user: demo@student.edu / DemoPass123!")
    print(f"MongoDB database: {settings.mongodb_db}")


if __name__ == "__main__":
    seed()
