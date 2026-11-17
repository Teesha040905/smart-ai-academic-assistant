"""Uploaded-file storage: local disk or MongoDB GridFS.

Set FILE_STORAGE=gridfs on hosts whose disk is wiped on restart (Render free tier, etc.).
The backend is chosen per file from its stored name, so files saved earlier keep working
after switching modes.
"""

from __future__ import annotations

import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional
from uuid import uuid4

from app.core.config import get_settings

GRIDFS_PREFIX = "gridfs:"
_BUCKET = "uploads"


def _bucket():
    import gridfs

    from app.core.database import get_database

    return gridfs.GridFSBucket(get_database(), bucket_name=_BUCKET)


def _local_root() -> Path:
    root = Path(get_settings().upload_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


def save(user_id: str, ext: str, content: bytes, *, filename: str, mime_type: str) -> str:
    """Store the file and return the reference to keep in ``documents.stored_filename``."""
    safe_name = f"{uuid4().hex}.{ext}"
    if get_settings().file_storage.lower() == "gridfs":
        file_id = _bucket().upload_from_stream(
            safe_name,
            content,
            metadata={"user_id": user_id, "original_filename": filename, "mime_type": mime_type},
        )
        return f"{GRIDFS_PREFIX}{file_id}"
    user_dir = _local_root() / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    (user_dir / safe_name).write_bytes(content)
    return f"{user_id}/{safe_name}"


def _gridfs_id(stored: str):
    from bson import ObjectId

    return ObjectId(stored[len(GRIDFS_PREFIX):])


def read_bytes(stored: str) -> Optional[bytes]:
    """Return the file's bytes, or None if it no longer exists."""
    if stored.startswith(GRIDFS_PREFIX):
        import gridfs

        try:
            return _bucket().open_download_stream(_gridfs_id(stored)).read()
        except gridfs.errors.NoFile:
            return None
    path = _local_root() / stored
    return path.read_bytes() if path.exists() else None


@contextmanager
def local_copy(stored: str, ext: str = "") -> Iterator[Path]:
    """Yield a filesystem path for the file (a temp copy for GridFS, named with ``ext``
    so type detection by suffix still works); raises FileNotFoundError if missing."""
    if not stored.startswith(GRIDFS_PREFIX):
        yield _local_root() / stored
        return
    data = read_bytes(stored)
    if data is None:
        raise FileNotFoundError(stored)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / (f"upload.{ext.lstrip('.')}" if ext else "upload")
        path.write_bytes(data)
        yield path


def delete(stored: str) -> None:
    if not stored:
        return
    if stored.startswith(GRIDFS_PREFIX):
        import gridfs

        try:
            _bucket().delete(_gridfs_id(stored))
        except gridfs.errors.NoFile:
            pass
        return
    (_local_root() / stored).unlink(missing_ok=True)
