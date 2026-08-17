import os
import shutil
from uuid import uuid4
from typing import IO
from fastapi import UploadFile
from app.core.logger import get_logger
from app.core.config import get_settings

settings = get_settings()
logger = get_logger(settings)


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def save_uploaded_file(upload_file: UploadFile, dest_dir: str) -> str:
    """Save an UploadFile to dest_dir and return the saved file path."""
    _ensure_dir(dest_dir)
    filename = upload_file.filename or "upload"
    _, ext = os.path.splitext(filename)
    safe_name = f"{uuid4().hex}{ext}"
    dest_path = os.path.join(dest_dir, safe_name)

    logger.debug("Saving uploaded file to %s", dest_path)
    with open(dest_path, "wb") as out_file:
        shutil.copyfileobj(upload_file.file, out_file)

    return dest_path
