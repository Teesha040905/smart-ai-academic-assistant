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
    debug: bool | str = True
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"
    cors_origins: str = "http://localhost:3000"
    # Optional regex for extra allowed origins, e.g. Vercel preview URLs:
    #   https://smart-ai-academic-assistant-.*\.vercel\.app
    cors_origin_regex: str = ""

    jwt_secret: str = "change-me-to-a-long-random-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7
    bcrypt_rounds: int = 12

    database_url: str = ""  # legacy; unused after MongoDB migration
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db: str = "smart_academic"

    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_collection: str = "academic_chunks"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    ai_api_key: str = ""
    ai_api_keys: str = ""
    ai_base_url: str = "https://api.openai.com/v1"
    ai_chat_model: str = "gpt-4o-mini"
    ai_embedding_model: str = "text-embedding-3-small"

    # "auto" = ChromaDB if installed, otherwise MongoDB; or force "chroma" / "mongo" / "memory"
    vector_store: str = "auto"

    upload_dir: str = "./uploads"
    # "local" = files on disk (UPLOAD_DIR); "gridfs" = files stored inside MongoDB (use on hosts
    # without a persistent disk, e.g. Render free tier)
    file_storage: str = "local"
    max_upload_mb: int = 25
    allowed_extensions: str = "pdf,docx,pptx,ppt,txt,png,jpg,jpeg,webp"

    redis_url: str = "redis://localhost:6379/0"
    rate_limit_per_minute: int = 60

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def allowed_extension_set(self) -> set[str]:
        return {e.strip().lower() for e in self.allowed_extensions.split(",") if e.strip()}

    @property
    def ai_api_key_list(self) -> List[str]:
        keys: List[str] = []
        if self.ai_api_keys:
            for k in self.ai_api_keys.split(","):
                k_clean = k.strip()
                if k_clean and k_clean not in keys:
                    keys.append(k_clean)
        if self.ai_api_key:
            for k in self.ai_api_key.split(","):
                k_clean = k.strip()
                if k_clean and k_clean not in keys:
                    keys.append(k_clean)
        return keys


_DEFAULT_JWT_SECRET = "change-me-to-a-long-random-secret"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.is_production and (
        settings.jwt_secret == _DEFAULT_JWT_SECRET or len(settings.jwt_secret) < 32
    ):
        raise RuntimeError("JWT_SECRET must be set to a random value of at least 32 characters in production")
    return settings
