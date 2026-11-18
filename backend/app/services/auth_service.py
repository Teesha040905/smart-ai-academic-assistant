from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from typing import Optional

from pymongo.database import Database

from app.core import file_storage
from app.core.errors import AppError
from app.core.security import create_access_token, hash_password, verify_password
from app.models import UserRole, make_password_reset, make_profile, make_user
from app.models.doc import Doc, from_mongo
from app.repositories import mongo as repo
from app.schemas import RegisterRequest, StudentProfileUpdate, UserUpdate


class AuthService:
    def __init__(self, db: Database):
        self.db = db

    def register(self, data: RegisterRequest) -> Doc:
        existing = repo.find_one(self.db, "users", {"email": data.email.lower()})
        if existing:
            raise AppError("Email already registered", status_code=409, code="email_taken")
        user = make_user(
            email=data.email.lower(),
            hashed_password=hash_password(data.password),
            full_name=data.full_name.strip(),
            role=UserRole.student,
        )
        repo.insert(self.db, "users", user)
        profile = make_profile(user_id=user.id, daily_study_hours=3.0)
        repo.insert(self.db, "student_profiles", profile)
        return self.get_user_with_profile(user.id)

    def authenticate(self, email: str, password: str) -> Doc:
        user = repo.find_one(self.db, "users", {"email": email.lower()})
        if not user or not verify_password(password, user.hashed_password):
            raise AppError("Invalid email or password", status_code=401, code="invalid_credentials")
        if not user.is_active:
            raise AppError("Account is disabled", status_code=403, code="inactive")
        return user

    def issue_token(self, user: Doc) -> str:
        role = user.role.value if hasattr(user.role, "value") else user.role
        # "tv" = token version; bumping it on the user (password reset) invalidates old tokens
        return create_access_token(user.id, extra={"role": role, "tv": getattr(user, "token_version", 0)})

    def get_user_with_profile(self, user_id: str) -> Doc:
        user = repo.find_one(self.db, "users", {"id": user_id})
        if not user:
            raise AppError("User not found", status_code=404)
        profile = repo.find_one(self.db, "student_profiles", {"user_id": user_id})
        user.profile = profile
        return user

    def update_user(self, user: Doc, data: UserUpdate) -> Doc:
        if data.full_name is not None:
            user.full_name = data.full_name.strip()
        if data.theme is not None:
            user.theme = data.theme
        repo.save(self.db, "users", user)
        return self.get_user_with_profile(user.id)

    def update_profile(self, user: Doc, data: StudentProfileUpdate) -> Doc:
        profile = repo.find_one(self.db, "student_profiles", {"user_id": user.id})
        if not profile:
            profile = make_profile(user_id=user.id)
            repo.insert(self.db, "student_profiles", profile)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)
        repo.save(self.db, "student_profiles", profile)
        return profile

    def request_password_reset(self, email: str) -> Optional[str]:
        user = repo.find_one(self.db, "users", {"email": email.lower()})
        if not user:
            return None
        raw = secrets.token_urlsafe(32)
        token = make_password_reset(
            user_id=user.id,
            token_hash=hashlib.sha256(raw.encode()).hexdigest(),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            used=False,
        )
        repo.insert(self.db, "password_reset_tokens", token)
        return raw

    def reset_password(self, raw_token: str, new_password: str) -> None:
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        token = repo.find_one(self.db, "password_reset_tokens", {"token_hash": token_hash, "used": False})
        expires_at = token.expires_at if token else None
        if expires_at is not None and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)  # MongoDB returns naive UTC datetimes
        if not token or expires_at < datetime.now(timezone.utc):
            raise AppError("Invalid or expired reset token", status_code=400)
        user = repo.find_one(self.db, "users", {"id": token.user_id})
        if not user:
            raise AppError("User not found", status_code=404)
        user.hashed_password = hash_password(new_password)
        user.token_version = getattr(user, "token_version", 0) + 1  # sign out all sessions
        repo.save(self.db, "users", user)
        token.used = True
        repo.save(self.db, "password_reset_tokens", token)

    def delete_account(self, user: Doc) -> None:
        uid = user.id
        # quiz_questions / quiz_answers carry no user_id, so remove them via their parents first
        quiz_ids = [q.id for q in repo.find_many(self.db, "quizzes", {"user_id": uid})]
        attempt_ids = [a.id for a in repo.find_many(self.db, "quiz_attempts", {"user_id": uid})]
        if quiz_ids:
            repo.delete_many(self.db, "quiz_questions", {"quiz_id": {"$in": quiz_ids}})
        if attempt_ids:
            repo.delete_many(self.db, "quiz_answers", {"attempt_id": {"$in": attempt_ids}})
        # uploaded files live outside the collections (disk or GridFS)
        for doc in repo.find_many(self.db, "documents", {"user_id": uid}):
            file_storage.delete(doc.stored_filename or "")
        collections = [
            "student_profiles",
            "subjects",
            "units",
            "topics",
            "documents",
            "document_chunks",
            "vector_chunks",
            "conversations",
            "messages",
            "study_plans",
            "study_sessions",
            "quizzes",
            "quiz_questions",
            "quiz_attempts",
            "quiz_answers",
            "flashcards",
            "exams",
            "assignments",
            "notifications",
            "recommendations",
            "study_activities",
            "password_reset_tokens",
        ]
        for name in collections:
            repo.delete_many(self.db, name, {"user_id": uid})
        repo.delete_one(self.db, "users", {"id": uid})
