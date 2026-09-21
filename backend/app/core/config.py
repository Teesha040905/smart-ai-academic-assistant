from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Smart AI Academic Assistant"
    environment: str = "development"
    debug: bool = True
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"
    cors_origins: str = "http://localhost:3000"

    jwt_secret: str = "change-me-to-a-long-random-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7
    bcrypt_rounds: int = 12

    database_url: str = "postgresql+psycopg://saa:saa_secret@localhost:5432/smart_academic"

    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_collection: str = "academic_chunks"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    ai_api_key: str = ""
    ai_base_url: str = "https://api.openai.com/v1"
    ai_chat_model: str = "gpt-4o-mini"
    ai_embedding_model: str = "text-embedding-3-small"

    upload_dir: str = "./uploads"
    max_upload_mb: int = 25
    allowed_extensions: str = "pdf,docx,pptx,ppt,txt,png,jpg,jpeg,webp"

    redis_url: str = "redis://localhost:6379/0"
    rate_limit_per_minute: int = 60

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def allowed_extension_set(self) -> set[str]:
        return {e.strip().lower() for e in self.allowed_extensions.split(",") if e.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
