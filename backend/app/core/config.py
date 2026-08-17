from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "VideoMind AI"
    environment: str = "development"
    debug: bool = True
    cors_origins: Optional[str] = "http://localhost:5173,http://127.0.0.1:5173"
    transcripts_dir: Optional[str] = "data/transcripts"
    whisper_model: Optional[str] = "small"
    max_duration_seconds: int = 60 * 60 * 6  # 6 hours
    # Scene detection / keyframes
    scenes_dir: Optional[str] = "data/scenes"
    keyframes_dir: Optional[str] = "data/keyframes"
    scene_threshold: float = 30.0
    max_scenes: int = 1000
    # Vision settings
    vision_model: Optional[str] = "dummy"
    vision_output_dir: Optional[str] = "data/vision"
    vision_max_image_size: int = 1024
    inference_device: Optional[str] = "cpu"
    # Events settings
    events_dir: Optional[str] = "data/events"
    minimum_event_duration: float = 0.5
    maximum_event_duration: float = 600.0
    # Semantic search settings
    embedding_model: Optional[str] = "BAAI/bge-small-en-v1.5"
    vector_db_path: Optional[str] = "data/vector_db"
    top_k_default: int = 5
    device: Optional[str] = "cpu"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
