from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings
from app.core.database import close_client, ensure_indexes, get_database, ping_mongo
from app.core.errors import AppError, SecurityHeadersMiddleware, app_error_handler, unhandled_error_handler
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()
    settings = get_settings()
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    ping_mongo()
    ensure_indexes(get_database())
    yield
    close_client()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        lifespan=lifespan,
        # API docs are only exposed outside production
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None if settings.is_production else "/redoc",
        openapi_url=None if settings.is_production else "/openapi.json",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        # Production: only CORS_ORIGINS (+ optional CORS_ORIGIN_REGEX). Development: any origin.
        allow_origin_regex=(settings.cors_origin_regex or None) if settings.is_production else r"https?://.*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
    app.include_router(router, prefix="/api/v1")

    @app.get("/health")
    @app.get("/api/v1/health")
    def health():
        try:
            ping_mongo.cache_clear()
            ping_mongo()
            db_status = "ok"
        except Exception:
            db_status = "unreachable"
        return {
            "status": "ok",
            "app": settings.app_name,
            "database": "mongodb",
            "db_status": db_status,
            "db_name": settings.mongodb_db,
        }

    return app


app = create_app()
