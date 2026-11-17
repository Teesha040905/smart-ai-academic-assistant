import re
from typing import Optional

from pymongo.database import Database

from app.core.errors import AppError
from app.models import TopicStatus, make_subject, make_topic, make_unit
from app.models.doc import Doc
from app.repositories import mongo as repo
from app.schemas import SubjectCreate, SubjectUpdate, TopicCreate, TopicUpdate, UnitCreate, UnitUpdate


def _topic_progress(topics: list[Doc]) -> float:
    if not topics:
        return 0.0
    return round(sum(t.knowledge_level for t in topics) / len(topics), 1)


class SubjectService:
    def __init__(self, db: Database):
        self.db = db

    def list_subjects(self, user: Doc) -> list[Doc]:
        subjects = repo.find_many(self.db, "subjects", {"user_id": user.id}, sort=[("name", 1)])
        for s in subjects:
            self._attach_tree(s)
        return subjects

    def get_owned(self, user: Doc, subject_id: str) -> Doc:
        subject = repo.find_one(self.db, "subjects", {"id": subject_id, "user_id": user.id})
        if not subject:
            raise AppError("Subject not found", status_code=404)
        self._attach_tree(subject)
        return subject

    def _attach_tree(self, subject: Doc) -> None:
        units = repo.find_many(
            self.db, "units", {"subject_id": subject.id}, sort=[("order_index", 1)]
        )
        topics = repo.find_many(self.db, "topics", {"subject_id": subject.id})
        by_unit: dict[str, list[Doc]] = {}
        for t in topics:
            if t.unit_id:
                by_unit.setdefault(t.unit_id, []).append(t)
        for u in units:
            u.topics = by_unit.get(u.id, [])
        subject.units = units
        subject.topics = topics

    def _ensure_unique_name(self, user: Doc, name: str, exclude_id: str | None = None) -> None:
        query = {"user_id": user.id, "name": {"$regex": f"^{re.escape(name)}$", "$options": "i"}}
        if exclude_id:
            query["id"] = {"$ne": exclude_id}
        if repo.find_one(self.db, "subjects", query):
            raise AppError(f'You already have a subject named "{name}"', status_code=409, code="duplicate_subject")

    def create(self, user: Doc, data: SubjectCreate) -> Doc:
        self._ensure_unique_name(user, data.name)
        subject = make_subject(user_id=user.id, **data.model_dump())
        repo.insert(self.db, "subjects", subject)
        subject.units = []
        subject.topics = []
        return subject

    def update(self, user: Doc, subject_id: str, data: SubjectUpdate) -> Doc:
        subject = repo.find_one(self.db, "subjects", {"id": subject_id, "user_id": user.id})
        if not subject:
            raise AppError("Subject not found", status_code=404)
        if data.name:
            self._ensure_unique_name(user, data.name, exclude_id=subject_id)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(subject, k, v)
        repo.save(self.db, "subjects", subject)
        return self.get_owned(user, subject_id)

    def delete(self, user: Doc, subject_id: str) -> None:
        self.get_owned(user, subject_id)
        repo.delete_many(self.db, "topics", {"subject_id": subject_id, "user_id": user.id})
        repo.delete_many(self.db, "units", {"subject_id": subject_id, "user_id": user.id})
        repo.delete_one(self.db, "subjects", {"id": subject_id, "user_id": user.id})

    def add_unit(self, user: Doc, subject_id: str, data: UnitCreate) -> Doc:
        self.get_owned(user, subject_id)
        unit = make_unit(subject_id=subject_id, user_id=user.id, **data.model_dump())
        repo.insert(self.db, "units", unit)
        unit.topics = []
        return unit

    def update_unit(self, user: Doc, unit_id: str, data: UnitUpdate) -> Doc:
        unit = repo.find_one(self.db, "units", {"id": unit_id, "user_id": user.id})
        if not unit:
            raise AppError("Unit not found", status_code=404)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(unit, k, v)
        repo.save(self.db, "units", unit)
        unit.topics = repo.find_many(self.db, "topics", {"unit_id": unit.id})
        return unit

    def delete_unit(self, user: Doc, unit_id: str) -> None:
        unit = repo.find_one(self.db, "units", {"id": unit_id, "user_id": user.id})
        if not unit:
            raise AppError("Unit not found", status_code=404)
        repo.delete_many(self.db, "topics", {"unit_id": unit_id, "user_id": user.id})
        repo.delete_one(self.db, "units", {"id": unit_id, "user_id": user.id})

    def add_topic(self, user: Doc, subject_id: str, data: TopicCreate) -> Doc:
        self.get_owned(user, subject_id)
        if data.unit_id:
            unit = repo.find_one(self.db, "units", {"id": data.unit_id, "user_id": user.id})
            if not unit or unit.subject_id != subject_id:
                raise AppError("Unit not found for subject", status_code=400)
        topic = make_topic(user_id=user.id, subject_id=subject_id, **data.model_dump())
        repo.insert(self.db, "topics", topic)
        return topic

    def update_topic(self, user: Doc, topic_id: str, data: TopicUpdate) -> Doc:
        topic = repo.find_one(self.db, "topics", {"id": topic_id, "user_id": user.id})
        if not topic:
            raise AppError("Topic not found", status_code=404)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(topic, k, v)
        if data.knowledge_level is not None and data.knowledge_level >= 80:
            topic.status = TopicStatus.completed
        elif data.knowledge_level is not None and data.knowledge_level > 0:
            topic.status = TopicStatus.in_progress
        repo.save(self.db, "topics", topic)
        return topic

    def delete_topic(self, user: Doc, topic_id: str) -> None:
        topic = repo.find_one(self.db, "topics", {"id": topic_id, "user_id": user.id})
        if not topic:
            raise AppError("Topic not found", status_code=404)
        repo.delete_one(self.db, "topics", {"id": topic_id, "user_id": user.id})

    def serialize_subject(self, subject: Doc) -> dict:
        if not hasattr(subject, "units") or subject.units is None:
            self._attach_tree(subject)
        units_out = []
        for unit in subject.units:
            unit_topics = getattr(unit, "topics", None) or []
            progress = (
                unit.progress_override
                if unit.progress_override is not None
                else _topic_progress(unit_topics)
            )
            units_out.append(
                {
                    "id": unit.id,
                    "subject_id": unit.subject_id,
                    "name": unit.name,
                    "order_index": unit.order_index,
                    "progress_override": unit.progress_override,
                    "progress": progress,
                    "topics": unit_topics,
                }
            )
        return {
            "id": subject.id,
            "name": subject.name,
            "code": subject.code,
            "description": subject.description,
            "color": subject.color,
            "priority": subject.priority,
            "exam_date": subject.exam_date,
            "progress": _topic_progress(subject.topics),
            "units": units_out,
            "topics": subject.topics,
        }
