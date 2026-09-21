from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.core.errors import AppError
from app.core.security import create_access_token, hash_password, verify_password
from app.models import PasswordResetToken, StudentProfile, User, UserRole
from app.schemas import RegisterRequest, StudentProfileUpdate, UserUpdate


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register(self, data: RegisterRequest) -> User:
        existing = self.db.query(User).filter(User.email == data.email.lower()).first()
        if existing:
            raise AppError("Email already registered", status_code=409, code="email_taken")
        user = User(
            email=data.email.lower(),
            hashed_password=hash_password(data.password),
            full_name=data.full_name.strip(),
            role=UserRole.student,
        )
        self.db.add(user)
        self.db.flush()
        profile = StudentProfile(user_id=user.id, daily_study_hours=3.0)
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate(self, email: str, password: str) -> User:
        user = self.db.query(User).filter(User.email == email.lower()).first()
        if not user or not verify_password(password, user.hashed_password):
            raise AppError("Invalid email or password", status_code=401, code="invalid_credentials")
        if not user.is_active:
            raise AppError("Account is disabled", status_code=403, code="inactive")
        return user

    def issue_token(self, user: User) -> str:
        return create_access_token(user.id, extra={"role": user.role.value})

    def get_user_with_profile(self, user_id: str) -> User:
        user = (
            self.db.query(User)
            .options(joinedload(User.profile))
            .filter(User.id == user_id)
            .first()
        )
        if not user:
            raise AppError("User not found", status_code=404)
        return user

    def update_user(self, user: User, data: UserUpdate) -> User:
        if data.full_name is not None:
            user.full_name = data.full_name.strip()
        if data.theme is not None:
            user.theme = data.theme
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_profile(self, user: User, data: StudentProfileUpdate) -> StudentProfile:
        profile = user.profile
        if not profile:
            profile = StudentProfile(user_id=user.id)
            self.db.add(profile)
            self.db.flush()
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def request_password_reset(self, email: str) -> Optional[str]:
        """Returns reset token in development for testing; production would email it."""
        user = self.db.query(User).filter(User.email == email.lower()).first()
        if not user:
            return None
        raw = secrets.token_urlsafe(32)
        token = PasswordResetToken(
            user_id=user.id,
            token_hash=hashlib.sha256(raw.encode()).hexdigest(),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        self.db.add(token)
        self.db.commit()
        return raw

    def reset_password(self, raw_token: str, new_password: str) -> None:
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        token = (
            self.db.query(PasswordResetToken)
            .filter(PasswordResetToken.token_hash == token_hash, PasswordResetToken.used.is_(False))
            .first()
        )
        if not token or token.expires_at < datetime.now(timezone.utc):
            raise AppError("Invalid or expired reset token", status_code=400)
        user = self.db.get(User, token.user_id)
        if not user:
            raise AppError("User not found", status_code=404)
        user.hashed_password = hash_password(new_password)
        token.used = True
        self.db.commit()

    def delete_account(self, user: User) -> None:
        self.db.delete(user)
        self.db.commit()
