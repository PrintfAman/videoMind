from fastapi import UploadFile
from typing import List
import os

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".mpg", ".mpeg"}
MAX_FILE_SIZE = 1024 * 1024 * 1024 * 2  # 2 GB


def _get_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()


def validate_video_upload(upload_file: UploadFile) -> None:
    if not upload_file.filename:
        raise ValueError("Missing filename")

    ext = _get_extension(upload_file.filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file extension: {ext}")

    if upload_file.content_type is None or not upload_file.content_type.startswith("video"):
        raise ValueError(f"Invalid content_type: {upload_file.content_type}")

    # Note: UploadFile streams; size check may require reading. Leave a lightweight check for now.
