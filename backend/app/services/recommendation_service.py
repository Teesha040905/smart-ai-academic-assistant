"""Deterministic recommendation & readiness engine.

Academic priority rules are code-based and testable. LLMs may only enrich wording.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    Assignment,
    AssignmentStatus,
    Exam,
    Flashcard,
    Priority,
    QuizAttempt,
    Recommendation,
    SessionStatus,
    StudyActivity,
    StudySession,
    Topic,
    User,
)


def days_until(d: date) -> int:
    return (d - date.today()).days


def compute_exam_readiness(db: Session, user: User, exam: Exam) -> dict[str, Any]:
    topics = db.query(Topic).filter(Topic.user_id == user.id, Topic.subject_id == exam.subject_id).all()
    syllabus = round(sum(t.knowledge_level for t in topics) / len(topics), 1) if topics else 0.0

    attempts = (
        db.query(QuizAttempt)
        .join(QuizAttempt.quiz)
        .filter(QuizAttempt.user_id == user.id)
        .all()
    )
    # Filter by subject via quiz — load simply
    from app.models import Quiz

    subject_attempts = (
        db.query(QuizAttempt)
        .join(Quiz, QuizAttempt.quiz_id == Quiz.id)
        .filter(QuizAttempt.user_id == user.id, Quiz.subject_id == exam.subject_id)
        .all()
    )
    quiz_perf = (
        round(sum(a.percentage for a in subject_attempts) / len(subject_attempts), 1)
        if subject_attempts
        else 0.0
    )

    revisions = sum(t.revision_count for t in topics)
    revision_score = min(100.0, revisions * 8.0) if topics else 0.0

    flash_count = (
        db.query(func.count(Flashcard.id))
        .filter(Flashcard.user_id == user.id, Flashcard.subject_id == exam.subject_id)
        .scalar()
        or 0
    )
    practice = min(100.0, flash_count * 5.0 + quiz_perf * 0.3)

    proximity = days_until(exam.exam_date)
    # Soft weight — readiness is preparation quality, not time remaining
    overall = round(
        syllabus * 0.35 + quiz_perf * 0.30 + revision_score * 0.20 + practice * 0.15,
        1,
    )

    return {
        "overall": overall,
        "syllabus_coverage": syllabus,
        "quiz_performance": quiz_perf,
        "revision": round(revision_score, 1),
        "practice": round(practice, 1),
        "days_remaining": proximity,
        "explanation": (
            "Readiness blends syllabus coverage (35%), quiz performance (30%), "
            "revision activity (20%), and practice volume (15%). "
            "It is not a prediction of exam marks."
        ),
    }


class RecommendationEngine:
    def __init__(self, db: Session):
        self.db = db

    def weak_topics(self, user: User, limit: int = 8) -> list[dict[str, Any]]:
        topics = (
            self.db.query(Topic)
            .filter(Topic.user_id == user.id)
            .order_by(Topic.knowledge_level.asc())
            .limit(limit)
            .all()
        )
        result = []
        for t in topics:
            level = t.knowledge_level
            status = "critical" if level < 55 else "warning" if level < 75 else "good"
            result.append(
                {
                    "id": t.id,
                    "name": t.name,
                    "subject_id": t.subject_id,
                    "knowledge_level": level,
                    "status": status,
                    "quiz_average": t.quiz_average,
                }
            )
        return result

    def generate(self, user: User) -> list[Recommendation]:
        """Rebuild active recommendations from deterministic rules."""
        # Soft-delete old by dismissing previous open ones
        old = (
            self.db.query(Recommendation)
            .filter(Recommendation.user_id == user.id, Recommendation.is_dismissed.is_(False))
            .all()
        )
        for r in old:
            r.is_dismissed = True

        candidates: list[tuple[float, dict[str, Any]]] = []
        topics = self.db.query(Topic).filter(Topic.user_id == user.id).all()
        exams = self.db.query(Exam).filter(Exam.user_id == user.id).all()
        exam_by_subject = {e.subject_id: e for e in exams}

        for topic in topics:
            score = 0.0
            reasons: list[str] = []
            exam = exam_by_subject.get(topic.subject_id)
            days = days_until(exam.exam_date) if exam else None

            if topic.knowledge_level < 60:
                score += (60 - topic.knowledge_level) * 1.5
                reasons.append(f"Knowledge level is {topic.knowledge_level:.0f}%")

            if topic.quiz_average is not None and topic.quiz_average < 60:
                score += (60 - topic.quiz_average) * 1.2
                reasons.append(f"Recent quiz average: {topic.quiz_average:.0f}%")

            if days is not None and days <= 7:
                score += max(0, (8 - days) * 12)
                reasons.append(f"Exam in {days} day(s)")

            if topic.last_studied_at:
                last = topic.last_studied_at
                if last.tzinfo is None:
                    last = last.replace(tzinfo=timezone.utc)
                lag = (datetime.now(timezone.utc) - last).days
                if lag >= 4:
                    score += min(30, lag * 4)
                    reasons.append(f"Last revision: {lag} days ago")
            else:
                score += 15
                reasons.append("Never studied yet")

            score *= topic.importance

            if score < 25:
                continue

            actions = []
            if topic.knowledge_level < 60:
                actions.append({"minutes": 30, "action": "revision", "label": f"{topic.name} revision"})
                actions.append({"minutes": 20, "action": "quiz", "label": "Practice questions"})
                actions.append({"minutes": 15, "action": "flashcards", "label": "Flashcard review"})
            else:
                actions.append({"minutes": 25, "action": "revision", "label": f"{topic.name} review"})
                actions.append({"minutes": 15, "action": "flashcards", "label": "Flashcards"})

            priority = Priority.high if score >= 80 else Priority.medium if score >= 50 else Priority.low
            candidates.append(
                (
                    score,
                    {
                        "topic_id": topic.id,
                        "subject_id": topic.subject_id,
                        "priority": priority,
                        "title": f"Focus on {topic.name}",
                        "reason": ". ".join(reasons),
                        "suggested_actions_json": json.dumps(actions),
                        "score": round(score, 1),
                    },
                )
            )

        # Assignment urgency
        assignments = (
            self.db.query(Assignment)
            .filter(
                Assignment.user_id == user.id,
                Assignment.status.in_([AssignmentStatus.pending, AssignmentStatus.in_progress]),
            )
            .all()
        )
        for a in assignments:
            rem = (a.deadline.date() - date.today()).days
            if rem <= 3:
                candidates.append(
                    (
                        90 - rem * 10,
                        {
                            "topic_id": None,
                            "subject_id": a.subject_id,
                            "priority": Priority.high,
                            "title": f"Assignment due: {a.title}",
                            "reason": f"Deadline in {rem} day(s)",
                            "suggested_actions_json": json.dumps(
                                [{"minutes": 45, "action": "assignment", "label": a.title}]
                            ),
                            "score": float(90 - rem * 10),
                        },
                    )
                )

        candidates.sort(key=lambda x: x[0], reverse=True)
        created: list[Recommendation] = []
        for score, payload in candidates[:8]:
            rec = Recommendation(user_id=user.id, **payload)
            self.db.add(rec)
            created.append(rec)

        self.db.commit()
        for r in created:
            self.db.refresh(r)
        return created

    def top_recommendation(self, user: User) -> Optional[Recommendation]:
        rec = (
            self.db.query(Recommendation)
            .filter(Recommendation.user_id == user.id, Recommendation.is_dismissed.is_(False))
            .order_by(Recommendation.score.desc())
            .first()
        )
        if not rec:
            generated = self.generate(user)
            return generated[0] if generated else None
        return rec


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def study_streak(self, user: User) -> dict[str, Any]:
        days = (
            self.db.query(StudyActivity.activity_date)
            .filter(StudyActivity.user_id == user.id, StudyActivity.minutes > 0)
            .distinct()
            .order_by(StudyActivity.activity_date.desc())
            .all()
        )
        dates = [d[0] for d in days]
        streak = 0
        cursor = date.today()
        date_set = set(dates)
        # Allow yesterday start if no activity today yet
        if cursor not in date_set and (cursor.toordinal() - 1) in {d.toordinal() for d in date_set}:
            cursor = date.fromordinal(cursor.toordinal() - 1)
        while cursor in date_set:
            streak += 1
            cursor = date.fromordinal(cursor.toordinal() - 1)

        week_start = date.fromordinal(date.today().toordinal() - date.today().weekday())
        sessions_done = (
            self.db.query(func.count(StudySession.id))
            .filter(
                StudySession.user_id == user.id,
                StudySession.status == SessionStatus.completed,
                StudySession.scheduled_date >= week_start,
            )
            .scalar()
            or 0
        )
        return {
            "streak_days": streak,
            "weekly_sessions_done": sessions_done,
            "weekly_goal": 10,
        }

    def dashboard_stats(self, user: User) -> dict[str, Any]:
        topics = self.db.query(Topic).filter(Topic.user_id == user.id).all()
        overall = round(sum(t.knowledge_level for t in topics) / len(topics), 1) if topics else 0.0
        hours = (
            self.db.query(func.coalesce(func.sum(StudyActivity.minutes), 0))
            .filter(StudyActivity.user_id == user.id)
            .scalar()
            or 0
        ) / 60.0
        attempts = self.db.query(QuizAttempt).filter(QuizAttempt.user_id == user.id).all()
        quiz_avg = (
            round(sum(a.percentage for a in attempts) / len(attempts), 1) if attempts else 0.0
        )
        tasks = (
            self.db.query(func.count(Assignment.id))
            .filter(Assignment.user_id == user.id, Assignment.status == AssignmentStatus.completed)
            .scalar()
            or 0
        )
        exams = self.db.query(Exam).filter(Exam.user_id == user.id).all()
        readiness_vals = []
        for e in exams:
            readiness_vals.append(compute_exam_readiness(self.db, user, e)["overall"])
        exam_readiness = round(sum(readiness_vals) / len(readiness_vals), 1) if readiness_vals else overall

        return {
            "overall_progress": overall,
            "study_hours": round(hours, 1),
            "quiz_average": quiz_avg,
            "tasks_completed": tasks,
            "exam_readiness": exam_readiness,
        }

    def full_analytics(self, user: User) -> dict[str, Any]:
        from app.models import Subject

        topics = self.db.query(Topic).filter(Topic.user_id == user.id).all()
        subjects = self.db.query(Subject).filter(Subject.user_id == user.id).all()
        subject_perf = []
        for s in subjects:
            st = [t for t in topics if t.subject_id == s.id]
            subject_perf.append(
                {
                    "id": s.id,
                    "name": s.name,
                    "progress": round(sum(t.knowledge_level for t in st) / len(st), 1) if st else 0.0,
                }
            )
        topic_perf = [
            {"id": t.id, "name": t.name, "subject_id": t.subject_id, "knowledge_level": t.knowledge_level}
            for t in sorted(topics, key=lambda x: x.knowledge_level)
        ]
        stats = self.dashboard_stats(user)
        completed = len([t for t in topics if t.knowledge_level >= 80])
        remaining = len(topics) - completed

        # Weekly progress last 7 days
        weekly = []
        for i in range(6, -1, -1):
            d = date.fromordinal(date.today().toordinal() - i)
            mins = (
                self.db.query(func.coalesce(func.sum(StudyActivity.minutes), 0))
                .filter(StudyActivity.user_id == user.id, StudyActivity.activity_date == d)
                .scalar()
                or 0
            )
            weekly.append({"date": d.isoformat(), "minutes": mins})

        monthly = []
        for i in range(29, -1, -1):
            d = date.fromordinal(date.today().toordinal() - i)
            mins = (
                self.db.query(func.coalesce(func.sum(StudyActivity.minutes), 0))
                .filter(StudyActivity.user_id == user.id, StudyActivity.activity_date == d)
                .scalar()
                or 0
            )
            monthly.append({"date": d.isoformat(), "minutes": mins})

        revisions = sum(t.revision_count for t in topics)
        active_days = len({w["date"] for w in weekly if w["minutes"] > 0})

        return {
            "overall_progress": stats["overall_progress"],
            "subject_performance": subject_perf,
            "topic_performance": topic_perf,
            "study_hours": stats["study_hours"],
            "quiz_average": stats["quiz_average"],
            "assignments_completed": stats["tasks_completed"],
            "topics_completed": completed,
            "topics_remaining": remaining,
            "weekly_progress": weekly,
            "monthly_progress": monthly,
            "revision_frequency": round(revisions / max(len(topics), 1), 2),
            "study_consistency": round(active_days / 7 * 100, 1),
        }

    def knowledge_map(self, user: User) -> dict[str, Any]:
        from app.models import Subject, Unit

        subjects = (
            self.db.query(Subject)
            .filter(Subject.user_id == user.id)
            .all()
        )
        tree = []
        for s in subjects:
            units = (
                self.db.query(Unit)
                .filter(Unit.subject_id == s.id, Unit.user_id == user.id)
                .order_by(Unit.order_index)
                .all()
            )
            unit_nodes = []
            for u in units:
                topics = (
                    self.db.query(Topic)
                    .filter(Topic.unit_id == u.id, Topic.user_id == user.id)
                    .all()
                )
                unit_nodes.append(
                    {
                        "id": u.id,
                        "name": u.name,
                        "topics": [
                            {
                                "id": t.id,
                                "name": t.name,
                                "knowledge_level": t.knowledge_level,
                                "status": (
                                    "critical"
                                    if t.knowledge_level < 55
                                    else "warning"
                                    if t.knowledge_level < 75
                                    else "good"
                                ),
                            }
                            for t in topics
                        ],
                    }
                )
            orphan = (
                self.db.query(Topic)
                .filter(Topic.subject_id == s.id, Topic.unit_id.is_(None), Topic.user_id == user.id)
                .all()
            )
            tree.append(
                {
                    "id": s.id,
                    "name": s.name,
                    "units": unit_nodes,
                    "topics": [
                        {
                            "id": t.id,
                            "name": t.name,
                            "knowledge_level": t.knowledge_level,
                            "status": (
                                "critical"
                                if t.knowledge_level < 55
                                else "warning"
                                if t.knowledge_level < 75
                                else "good"
                            ),
                        }
                        for t in orphan
                    ],
                }
            )
        return {"subjects": tree}
