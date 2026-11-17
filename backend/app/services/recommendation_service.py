"""Deterministic recommendation & readiness engine (MongoDB)."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Any, Optional

from pymongo.database import Database

from app.models import AssignmentStatus, Priority, SessionStatus, make_recommendation
from app.models.doc import Doc
from app.repositories import mongo as repo


def days_until(d: date) -> int:
    return (d - date.today()).days


def compute_exam_readiness(db: Database, user: Doc, exam: Doc) -> dict[str, Any]:
    topics = repo.find_many(db, "topics", {"user_id": user.id, "subject_id": exam.subject_id})
    syllabus = round(sum(t.knowledge_level for t in topics) / len(topics), 1) if topics else 0.0

    quizzes = repo.find_many(db, "quizzes", {"user_id": user.id, "subject_id": exam.subject_id})
    quiz_ids = [q.id for q in quizzes]
    subject_attempts = []
    for qid in quiz_ids:
        subject_attempts.extend(repo.find_many(db, "quiz_attempts", {"user_id": user.id, "quiz_id": qid}))

    quiz_perf = (
        round(sum(a.percentage for a in subject_attempts) / len(subject_attempts), 1)
        if subject_attempts
        else 0.0
    )

    revisions = sum(t.revision_count for t in topics)
    revision_score = min(100.0, revisions * 8.0) if topics else 0.0

    flash_count = repo.count(db, "flashcards", {"user_id": user.id, "subject_id": exam.subject_id})
    practice = min(100.0, flash_count * 5.0 + quiz_perf * 0.3)
    proximity = days_until(exam.exam_date)
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
    def __init__(self, db: Database):
        self.db = db

    def weak_topics(self, user: Doc, limit: int = 8) -> list[dict[str, Any]]:
        topics = repo.find_many(
            self.db, "topics", {"user_id": user.id}, sort=[("knowledge_level", 1)], limit=limit
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

    def generate(self, user: Doc) -> list[Doc]:
        old = repo.find_many(self.db, "recommendations", {"user_id": user.id, "is_dismissed": False})
        for r in old:
            r.is_dismissed = True
            repo.save(self.db, "recommendations", r)

        candidates: list[tuple[float, dict[str, Any]]] = []
        topics = repo.find_many(self.db, "topics", {"user_id": user.id})
        exams = repo.find_many(self.db, "exams", {"user_id": user.id})
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
                if getattr(last, "tzinfo", None) is None:
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

        subjects_with_topics = {t.subject_id for t in topics}
        for subject in repo.find_many(self.db, "subjects", {"user_id": user.id}):
            if subject.id in subjects_with_topics:
                continue
            candidate = self._subject_candidate(user, subject, exam_by_subject.get(subject.id))
            if candidate:
                candidates.append(candidate)

        assignments = repo.find_many(
            self.db,
            "assignments",
            {
                "user_id": user.id,
                "status": {"$in": [AssignmentStatus.pending.value, AssignmentStatus.in_progress.value]},
            },
        )
        for a in assignments:
            deadline = a.deadline
            if isinstance(deadline, str):
                deadline = datetime.fromisoformat(deadline)
            rem = (deadline.date() - date.today()).days if hasattr(deadline, "date") else 0
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
        created: list[Doc] = []
        for _, payload in candidates[:8]:
            rec = make_recommendation(user_id=user.id, **payload)
            repo.insert(self.db, "recommendations", rec)
            created.append(rec)
        return created

    def _subject_candidate(
        self, user: Doc, subject: Doc, exam: Optional[Doc]
    ) -> Optional[tuple[float, dict[str, Any]]]:
        """Score a subject that has no topic breakdown, using its quizzes, exam and activity."""
        score = 0.0
        reasons: list[str] = []

        quiz_ids = [
            q.id for q in repo.find_many(self.db, "quizzes", {"user_id": user.id, "subject_id": subject.id})
        ]
        attempts = (
            repo.find_many(self.db, "quiz_attempts", {"user_id": user.id, "quiz_id": {"$in": quiz_ids}})
            if quiz_ids
            else []
        )
        quiz_avg = round(sum(a.percentage for a in attempts) / len(attempts), 1) if attempts else None
        if quiz_avg is None:
            score += 40
            reasons.append("No quizzes taken yet")
        elif quiz_avg < 60:
            score += (60 - quiz_avg) * 1.5
            reasons.append(f"Quiz average: {quiz_avg:.0f}%")

        if exam:
            days = days_until(exam.exam_date)
            if days <= 7:
                score += max(0, (8 - days) * 12)
                reasons.append(f"Exam in {days} day(s)")

        activities = repo.find_many(
            self.db,
            "study_activities",
            {"user_id": user.id, "subject_id": subject.id},
            sort=[("activity_date", -1)],
            limit=1,
        )
        if activities:
            last = activities[0].activity_date
            if isinstance(last, datetime):
                last = last.date()
            elif isinstance(last, str):
                last = date.fromisoformat(last[:10])
            lag = (date.today() - last).days
            if lag >= 4:
                score += min(30, lag * 4)
                reasons.append(f"Last studied: {lag} days ago")
        else:
            score += 15
            reasons.append("Never studied yet")

        if score < 25:
            return None

        actions = [
            {"minutes": 20, "action": "quiz", "label": f"Practice quiz on {subject.name}"},
            {"minutes": 15, "action": "flashcards", "label": "Flashcard review"},
            {"minutes": 5, "action": "topics", "label": f"Add topics to {subject.name} for sharper advice"},
        ]
        priority = Priority.high if score >= 80 else Priority.medium if score >= 50 else Priority.low
        return (
            score,
            {
                "topic_id": None,
                "subject_id": subject.id,
                "priority": priority,
                "title": f"Practise {subject.name}",
                "reason": ". ".join(reasons),
                "suggested_actions_json": json.dumps(actions),
                "score": round(score, 1),
            },
        )

    def top_recommendation(self, user: Doc) -> Optional[Doc]:
        recs = repo.find_many(
            self.db,
            "recommendations",
            {"user_id": user.id, "is_dismissed": False},
            sort=[("score", -1)],
            limit=1,
        )
        if recs:
            return recs[0]
        generated = self.generate(user)
        return generated[0] if generated else None


class AnalyticsService:
    def __init__(self, db: Database):
        self.db = db

    def study_streak(self, user: Doc) -> dict[str, Any]:
        activities = repo.find_many(
            self.db,
            "study_activities",
            {"user_id": user.id, "minutes": {"$gt": 0}},
            sort=[("activity_date", -1)],
        )
        dates = sorted({a.activity_date for a in activities}, reverse=True)
        streak = 0
        cursor = date.today()
        date_set = set(dates)
        if cursor not in date_set and date.fromordinal(cursor.toordinal() - 1) in date_set:
            cursor = date.fromordinal(cursor.toordinal() - 1)
        while cursor in date_set:
            streak += 1
            cursor = date.fromordinal(cursor.toordinal() - 1)

        week_start = date.fromordinal(date.today().toordinal() - date.today().weekday())
        sessions = repo.find_many(
            self.db,
            "study_sessions",
            {
                "user_id": user.id,
                "status": SessionStatus.completed.value,
                "scheduled_date": {"$gte": week_start.isoformat()},
            },
        )
        # also match date objects if stored that way
        sessions_done = len(sessions)
        if sessions_done == 0:
            all_completed = repo.find_many(
                self.db,
                "study_sessions",
                {"user_id": user.id, "status": SessionStatus.completed.value},
            )
            sessions_done = sum(1 for s in all_completed if s.scheduled_date >= week_start)

        return {
            "streak_days": streak,
            "weekly_sessions_done": sessions_done,
            "weekly_goal": 10,
        }

    def dashboard_stats(self, user: Doc) -> dict[str, Any]:
        topics = repo.find_many(self.db, "topics", {"user_id": user.id})
        overall = round(sum(t.knowledge_level for t in topics) / len(topics), 1) if topics else 0.0
        activities = repo.find_many(self.db, "study_activities", {"user_id": user.id})
        hours = sum(a.minutes for a in activities) / 60.0
        attempts = repo.find_many(self.db, "quiz_attempts", {"user_id": user.id})
        quiz_avg = (
            round(sum(a.percentage for a in attempts) / len(attempts), 1) if attempts else 0.0
        )
        tasks = repo.count(
            self.db, "assignments", {"user_id": user.id, "status": AssignmentStatus.completed.value}
        )
        exams = repo.find_many(self.db, "exams", {"user_id": user.id})
        readiness_vals = [compute_exam_readiness(self.db, user, e)["overall"] for e in exams]
        exam_readiness = (
            round(sum(readiness_vals) / len(readiness_vals), 1) if readiness_vals else overall
        )
        return {
            "overall_progress": overall,
            "study_hours": round(hours, 1),
            "quiz_average": quiz_avg,
            "tasks_completed": tasks,
            "exam_readiness": exam_readiness,
        }

    def full_analytics(self, user: Doc) -> dict[str, Any]:
        topics = repo.find_many(self.db, "topics", {"user_id": user.id})
        subjects = repo.find_many(self.db, "subjects", {"user_id": user.id})
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
            {
                "id": t.id,
                "name": t.name,
                "subject_id": t.subject_id,
                "knowledge_level": t.knowledge_level,
            }
            for t in sorted(topics, key=lambda x: x.knowledge_level)
        ]
        stats = self.dashboard_stats(user)
        completed = len([t for t in topics if t.knowledge_level >= 80])
        remaining = len(topics) - completed

        activities = repo.find_many(self.db, "study_activities", {"user_id": user.id})
        by_day = {}
        for a in activities:
            key = a.activity_date.isoformat() if hasattr(a.activity_date, "isoformat") else str(a.activity_date)
            by_day[key] = by_day.get(key, 0) + a.minutes

        weekly = []
        for i in range(6, -1, -1):
            d = date.fromordinal(date.today().toordinal() - i)
            weekly.append({"date": d.isoformat(), "minutes": by_day.get(d.isoformat(), 0)})
        monthly = []
        for i in range(29, -1, -1):
            d = date.fromordinal(date.today().toordinal() - i)
            monthly.append({"date": d.isoformat(), "minutes": by_day.get(d.isoformat(), 0)})

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

    def knowledge_map(self, user: Doc) -> dict[str, Any]:
        subjects = repo.find_many(self.db, "subjects", {"user_id": user.id})
        tree = []
        for s in subjects:
            units = repo.find_many(
                self.db, "units", {"subject_id": s.id, "user_id": user.id}, sort=[("order_index", 1)]
            )
            unit_nodes = []
            for u in units:
                topics = repo.find_many(self.db, "topics", {"unit_id": u.id, "user_id": user.id})
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
            orphan = repo.find_many(
                self.db,
                "topics",
                {"subject_id": s.id, "user_id": user.id, "unit_id": None},
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
