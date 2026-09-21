from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.core.errors import AppError
from app.models import Subject, Topic, TopicStatus, Unit, User
from app.schemas import SubjectCreate, SubjectUpdate, TopicCreate, TopicUpdate, UnitCreate, UnitUpdate


def _topic_progress(topics: list[Topic]) -> float:
    if not topics:
        return 0.0
    return round(sum(t.knowledge_level for t in topics) / len(topics), 1)


class SubjectService:
    def __init__(self, db: Session):
        self.db = db

    def list_subjects(self, user: User) -> list[Subject]:
        return (
            self.db.query(Subject)
            .options(joinedload(Subject.units).joinedload(Unit.topics), joinedload(Subject.topics))
            .filter(Subject.user_id == user.id)
            .order_by(Subject.name)
            .all()
        )

    def get_owned(self, user: User, subject_id: str) -> Subject:
        subject = (
            self.db.query(Subject)
            .options(joinedload(Subject.units).joinedload(Unit.topics), joinedload(Subject.topics))
            .filter(Subject.id == subject_id, Subject.user_id == user.id)
            .first()
        )
        if not subject:
            raise AppError("Subject not found", status_code=404)
        return subject

    def create(self, user: User, data: SubjectCreate) -> Subject:
        subject = Subject(user_id=user.id, **data.model_dump())
        self.db.add(subject)
        self.db.commit()
        self.db.refresh(subject)
        return subject

    def update(self, user: User, subject_id: str, data: SubjectUpdate) -> Subject:
        subject = self.get_owned(user, subject_id)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(subject, k, v)
        self.db.commit()
        return self.get_owned(user, subject_id)

    def delete(self, user: User, subject_id: str) -> None:
        subject = self.get_owned(user, subject_id)
        self.db.delete(subject)
        self.db.commit()

    def add_unit(self, user: User, subject_id: str, data: UnitCreate) -> Unit:
        self.get_owned(user, subject_id)
        unit = Unit(subject_id=subject_id, user_id=user.id, **data.model_dump())
        self.db.add(unit)
        self.db.commit()
        self.db.refresh(unit)
        return unit

    def update_unit(self, user: User, unit_id: str, data: UnitUpdate) -> Unit:
        unit = self.db.query(Unit).filter(Unit.id == unit_id, Unit.user_id == user.id).first()
        if not unit:
            raise AppError("Unit not found", status_code=404)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(unit, k, v)
        self.db.commit()
        self.db.refresh(unit)
        return unit

    def delete_unit(self, user: User, unit_id: str) -> None:
        unit = self.db.query(Unit).filter(Unit.id == unit_id, Unit.user_id == user.id).first()
        if not unit:
            raise AppError("Unit not found", status_code=404)
        self.db.delete(unit)
        self.db.commit()

    def add_topic(self, user: User, subject_id: str, data: TopicCreate) -> Topic:
        self.get_owned(user, subject_id)
        if data.unit_id:
            unit = self.db.query(Unit).filter(Unit.id == data.unit_id, Unit.user_id == user.id).first()
            if not unit or unit.subject_id != subject_id:
                raise AppError("Unit not found for subject", status_code=400)
        topic = Topic(user_id=user.id, subject_id=subject_id, **data.model_dump())
        self.db.add(topic)
        self.db.commit()
        self.db.refresh(topic)
        return topic

    def update_topic(self, user: User, topic_id: str, data: TopicUpdate) -> Topic:
        topic = self.db.query(Topic).filter(Topic.id == topic_id, Topic.user_id == user.id).first()
        if not topic:
            raise AppError("Topic not found", status_code=404)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(topic, k, v)
        if data.knowledge_level is not None and data.knowledge_level >= 80:
            topic.status = TopicStatus.completed
        elif data.knowledge_level is not None and data.knowledge_level > 0:
            topic.status = TopicStatus.in_progress
        self.db.commit()
        self.db.refresh(topic)
        return topic

    def delete_topic(self, user: User, topic_id: str) -> None:
        topic = self.db.query(Topic).filter(Topic.id == topic_id, Topic.user_id == user.id).first()
        if not topic:
            raise AppError("Topic not found", status_code=404)
        self.db.delete(topic)
        self.db.commit()

    def serialize_subject(self, subject: Subject) -> dict:
        units_out = []
        for unit in sorted(subject.units, key=lambda u: u.order_index):
            unit_topics = unit.topics
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
        all_topics = subject.topics
        return {
            "id": subject.id,
            "name": subject.name,
            "code": subject.code,
            "description": subject.description,
            "color": subject.color,
            "priority": subject.priority,
            "exam_date": subject.exam_date,
            "progress": _topic_progress(all_topics),
            "units": units_out,
            "topics": all_topics,
        }
