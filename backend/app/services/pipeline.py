import time
from typing import List
from dataclasses import dataclass, field
from app.core.logger import get_logger
from app.core.config import get_settings

settings = get_settings()
logger = get_logger(settings)


@dataclass
class ProcessingContext:
    video_id: str
    video_path: str
    metadata: dict | None = None
    audio_path: str | None = None
    transcript: dict | None = None
    scene_data: list = field(default_factory=list)
    processing_status: str | None = None
    execution_times: dict = field(default_factory=dict)
    results: dict = field(default_factory=dict)


class PipelineStage:
    name: str = "base"

    def execute(self, ctx: ProcessingContext) -> None:
        raise NotImplementedError()


class Pipeline:
    def __init__(self, stages: List[PipelineStage]):
        self.stages = stages

    def run(self, ctx: ProcessingContext) -> ProcessingContext:
        logger.info("Pipeline start for video_id=%s", ctx.video_id)
        for stage in self.stages:
            logger.info("Stage start: %s", stage.name)
            t0 = time.perf_counter()
            try:
                stage.execute(ctx)
            except Exception as e:
                logger.exception("Stage %s failed: %s", stage.name, e)
                ctx.processing_status = "failed"
                raise
            elapsed = time.perf_counter() - t0
            ctx.execution_times[stage.name] = elapsed
            logger.info("Stage complete: %s (%.3fs)", stage.name, elapsed)
        ctx.processing_status = "completed"
        logger.info("Pipeline completed for video_id=%s", ctx.video_id)
        return ctx
