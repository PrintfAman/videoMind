from typing import Dict, Any
from app.core.config import get_settings
from app.core.logger import get_logger
import threading

settings = get_settings()
logger = get_logger(settings)


class WhisperModelManager:
    _instance = None
    _lock = threading.Lock()

    def __init__(self, model_name: str):
        try:
            import whisper
        except Exception as e:
            logger.error("Whisper import failed: %s", e)
            raise
        logger.info("Loading whisper model: %s", model_name)
        self.model = whisper.load_model(model_name)

    @classmethod
    def get_instance(cls, model_name: str):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = WhisperModelManager(model_name)
        return cls._instance


def transcribe_audio(audio_path: str, language: str | None = None) -> Dict[str, Any]:
    model_name = settings.whisper_model
    manager = WhisperModelManager.get_instance(model_name)
    logger.info("Starting Whisper transcription for %s", audio_path)
    # model.transcribe returns dict with text, segments, language
    result = manager.model.transcribe(audio_path, language=language)
    logger.info("Whisper transcription completed for %s", audio_path)
    return result
