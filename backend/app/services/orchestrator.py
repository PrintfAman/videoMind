import time
import os
import json
from typing import Dict, Any
from app.core.logger import get_logger
from app.core.config import get_settings
from app.services import media
from app.services import whisper_service
from app.services.pipeline import ProcessingContext, Pipeline
from app.services.stages import MetadataStage, AudioExtractionStage, WhisperStage, SceneDetectionStage, KeyframeExtractionStage, VisionStage
from app.services.stages import EventStage

settings = get_settings()
logger = get_logger(settings)


class ProcessingError(Exception):
    pass


def _write_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def process_video(video_path: str, language: str | None = None) -> Dict[str, Any]:
    """Execute processing by constructing a Pipeline of stages and running it.

    Returns the pipeline results dictionary.
    """
    video_id = os.path.splitext(os.path.basename(video_path))[0]
    ctx = ProcessingContext(video_id=video_id, video_path=video_path)

    stages = [
        MetadataStage(),
        AudioExtractionStage(),
        WhisperStage(),
        SceneDetectionStage(),
        KeyframeExtractionStage(),
        VisionStage(),
        EventStage(),
    ]

    pipeline = Pipeline(stages)
    try:
        pipeline.run(ctx)
        # return structured results
        return {"video_path": video_path, "results": ctx.results, "times": ctx.execution_times}
    except Exception as e:
        logger.exception("Processing failed for %s: %s", video_path, e)
        raise ProcessingError(str(e)) from e
