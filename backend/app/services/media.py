import subprocess
import json
import shutil
from typing import Dict
from app.core.logger import get_logger
from app.core.config import get_settings

settings = get_settings()
logger = get_logger(settings)


def _find_executable(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"Required executable '{name}' not found in PATH")
    return path


def ffprobe_metadata(video_path: str) -> Dict:
    ffprobe = _find_executable("ffprobe")
    cmd = [ffprobe, "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", video_path]
    logger.debug("Running ffprobe: %s", cmd)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        logger.error("ffprobe failed: %s", proc.stderr)
        raise RuntimeError("ffprobe failed")
    return json.loads(proc.stdout or "{}")


def extract_audio(video_path: str, out_audio_path: str) -> None:
    ffmpeg = _find_executable("ffmpeg")
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        video_path,
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "44100",
        "-ac",
        "2",
        out_audio_path,
    ]
    logger.debug("Running ffmpeg: %s", cmd)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        logger.error("ffmpeg failed: %s", proc.stderr)
        raise RuntimeError("ffmpeg failed")
