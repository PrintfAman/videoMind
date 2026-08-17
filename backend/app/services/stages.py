import os
import json
import subprocess
import shutil
import time
from typing import Any
from app.services.pipeline import PipelineStage, ProcessingContext
from app.core.logger import get_logger
from app.core.config import get_settings
from app.services import media
from app.services import whisper_service
import app.services.vision as vision_module
from app.services.event_builder import build_events_for_video
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore

settings = get_settings()
logger = get_logger(settings)


class MetadataStage(PipelineStage):
    name = "metadata"

    def execute(self, ctx: ProcessingContext) -> None:
        metadata = media.ffprobe_metadata(ctx.video_path)
        ctx.metadata = metadata
        # persist metadata
        meta_dir = os.path.join(os.getcwd(), "data", "metadata")
        os.makedirs(meta_dir, exist_ok=True)
        meta_path = os.path.join(meta_dir, os.path.basename(ctx.video_path) + ".json")
        with open(meta_path, "w", encoding="utf-8") as fh:
            json.dump(metadata, fh, indent=2)
        ctx.results["metadata_path"] = meta_path
        logger.info("Metadata written to %s", meta_path)


class AudioExtractionStage(PipelineStage):
    name = "audio_extraction"

    def execute(self, ctx: ProcessingContext) -> None:
        out = os.path.join(os.getcwd(), "data", "audio", os.path.splitext(os.path.basename(ctx.video_path))[0] + ".wav")
        media.extract_audio(ctx.video_path, out)
        ctx.audio_path = out
        ctx.results["audio_path"] = out
        logger.info("Audio extracted to %s", out)


class WhisperStage(PipelineStage):
    name = "whisper"

    def execute(self, ctx: ProcessingContext) -> None:
        if not ctx.audio_path:
            raise RuntimeError("Audio not available for transcription")
        raw = whisper_service.transcribe_audio(ctx.audio_path)
        # assemble transcript object
        transcript = {
            "id": os.path.splitext(os.path.basename(ctx.video_path))[0],
            "language": raw.get("language"),
            "duration": float(ctx.metadata.get("format", {}).get("duration") or 0),
            "segments": [],
        }
        for seg in raw.get("segments", []):
            transcript["segments"].append({"start": float(seg.get("start", 0)), "end": float(seg.get("end", 0)), "text": seg.get("text", "").strip()})

        # persist transcript
        transcripts_dir = settings.transcripts_dir
        os.makedirs(transcripts_dir, exist_ok=True)
        transcript_path = os.path.join(transcripts_dir, transcript["id"] + ".json")
        with open(transcript_path, "w", encoding="utf-8") as fh:
            json.dump(transcript, fh, indent=2)
        ctx.transcript = transcript
        ctx.results["transcript_path"] = transcript_path
        logger.info("Transcript saved to %s", transcript_path)


class SceneDetectionStage(PipelineStage):
    name = "scene_detection"

    def execute(self, ctx: ProcessingContext) -> None:
        # Import PySceneDetect lazily. Support both legacy and modern API shapes.
        try:
            import scenedetect
            try:
                from scenedetect import VideoManager, SceneManager
                from scenedetect.detectors import ContentDetector
                video_manager = VideoManager([ctx.video_path])
                scene_manager = SceneManager()
                scene_manager.add_detector(ContentDetector(threshold=getattr(settings, "scene_threshold", 30.0)))
                video_manager.start()
                scene_manager.detect_scenes(frame_source=video_manager)
                scene_list = scene_manager.get_scene_list()
            except Exception:
                mod = scenedetect
                open_video = getattr(mod, "open_video", None)
                SceneManager = getattr(mod, "SceneManager", None)
                if open_video is None or SceneManager is None:
                    from scenedetect import open_video as real_open_video
                    from scenedetect.scene_manager import SceneManager
                else:
                    real_open_video = open_video
                from scenedetect.detectors import ContentDetector
                video_stream = real_open_video(ctx.video_path)
                scene_manager = SceneManager()
                scene_manager.add_detector(ContentDetector(threshold=getattr(settings, "scene_threshold", 30.0)))
                scene_manager.detect_scenes(video=video_stream)
                scene_list = scene_manager.get_scene_list()
        except Exception as e:
            logger.error("PySceneDetect import failed: %s", e)
            raise

        scenes = []
        for i, scene in enumerate(scene_list, start=1):
            # each scene is a (start, end) FrameTimecode pair
            try:
                start = scene[0].get_seconds()
                end = scene[1].get_seconds()
            except Exception:
                # fallback if get_seconds not available
                start = float(scene[0].get_timecode())
                end = float(scene[1].get_timecode())
            scenes.append({"scene_id": i, "start": float(start), "end": float(end), "duration": float(end - start)})

        # persist scenes individually and summary
        scenes_dir = os.path.abspath(os.path.join(os.getcwd(), getattr(settings, "scenes_dir", "data/scenes")))
        os.makedirs(scenes_dir, exist_ok=True)
        # per-scene files
        for s in scenes:
            per_path = os.path.join(scenes_dir, f"{ctx.video_id}_scene{s['scene_id']:03d}.json")
            with open(per_path, "w", encoding="utf-8") as fh:
                json.dump(s, fh, indent=2)

        # summary file
        summary = {"video_id": ctx.video_id, "scene_count": len(scenes), "scenes": [{"scene_id": s["scene_id"], "start": s["start"], "end": s["end"], "keyframe": f"{ctx.video_id}_scene{s['scene_id']:03d}.jpg"} for s in scenes]}
        summary_path = os.path.join(scenes_dir, ctx.video_id + ".json")
        with open(summary_path, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=2)

        ctx.scene_data = scenes
        ctx.results["scenes_summary"] = summary_path
        logger.info("Scene detection completed: %d scenes, summary=%s", len(scenes), summary_path)


class KeyframeExtractionStage(PipelineStage):
    name = "keyframe_extraction"

    def execute(self, ctx: ProcessingContext) -> None:
        if not ctx.scene_data:
            logger.info("No scenes present, skipping keyframe extraction")
            return
        keyframes_dir = os.path.abspath(os.path.join(os.getcwd(), getattr(settings, "keyframes_dir", "data/keyframes")))
        os.makedirs(keyframes_dir, exist_ok=True)
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise RuntimeError("ffmpeg executable not found")

        for scene in ctx.scene_data:
            scene_id = scene["scene_id"]
            start = scene["start"]
            end = scene["end"]
            mid = (start + end) / 2.0
            out_name = f"{ctx.video_id}_scene{scene_id:03d}.jpg"
            out_path = os.path.join(keyframes_dir, out_name)
            cmd = [
                ffmpeg,
                "-y",
                "-ss",
                str(mid),
                "-i",
                ctx.video_path,
                "-frames:v",
                "1",
                "-q:v",
                "2",
                out_path,
            ]
            logger.debug("Running ffmpeg for keyframe: %s", cmd)
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode != 0:
                logger.error("ffmpeg keyframe extraction failed: %s", proc.stderr)
                raise RuntimeError("ffmpeg keyframe extraction failed")
            # record created keyframe
            ctx.results.setdefault("keyframes", []).append(out_path)

        ctx.results.setdefault("keyframes_dir", os.path.abspath(keyframes_dir))
        logger.info("Keyframe extraction completed for %d scenes", len(ctx.scene_data))


class VisionStage(PipelineStage):
    name = "vision"

    def execute(self, ctx: ProcessingContext) -> None:
        # run vision analysis for each keyframe
        analyzer = vision_module.get_vision_analyzer()
        keyframes = ctx.results.get("keyframes", [])
        if not keyframes:
            logger.info("No keyframes available, skipping vision analysis")
            return

        vision_out_dir = os.path.abspath(os.path.join(os.getcwd(), getattr(settings, "vision_output_dir", "data/vision")))
        os.makedirs(vision_out_dir, exist_ok=True)

        vision_results = []
        max_size = getattr(settings, "vision_max_image_size", None)
        for i, kf in enumerate(keyframes, start=1):
            try:
                logger.info("Vision analyze start: %s", kf)
                t0 = __import__("time").perf_counter()
                vr = analyzer.analyze(kf, max_size)
                elapsed = __import__("time").perf_counter() - t0
                logger.info("Vision analyze complete: %s (%.3fs)", kf, elapsed)
                vision_results.append({
                    "scene_id": i,
                    "caption": vr.caption,
                    "objects": vr.objects,
                    "activities": vr.activities,
                    "scene_type": vr.scene_type,
                    "confidence": vr.confidence,
                })
            except Exception as e:
                logger.exception("Vision analysis failed for %s: %s", kf, e)
        # persist per-video vision JSON
        summary = {"video_id": ctx.video_id, "scenes": vision_results}
        out_path = os.path.join(vision_out_dir, ctx.video_id + ".json")
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=2)
        ctx.results["vision_path"] = out_path
        logger.info("Vision analysis completed: %d scenes, output=%s", len(vision_results), out_path)


class EventStage(PipelineStage):
    name = "event_builder"

    def execute(self, ctx: ProcessingContext) -> None:
        logger.info("Event building started for %s", ctx.video_id)
        try:
            out = build_events_for_video(ctx.video_id)
            ctx.results["events_path"] = out

            with open(out, "r", encoding="utf-8") as fh:
                data = json.load(fh)

            events = data.get("events", [])
            if events:
                embedding_service = EmbeddingService()
                vector_store = VectorStore(path=getattr(settings, "vector_db_path", "data/vector_db"), collection_name="video_events")
                vector_store.create_collection()
                for event in events:
                    text_fields = [
                        event.get("summary") or "",
                        event.get("speech") or "",
                        event.get("caption") or "",
                        event.get("scene_type") or "",
                        " ".join(event.get("objects", []) or []),
                        " ".join(event.get("activities", []) or []),
                    ]
                    text = " ".join(part for part in text_fields if part)
                    if not text:
                        text = f"video event {ctx.video_id} scene {event.get('scene_id')}"
                    start_t = time.perf_counter()
                    embedding = embedding_service.embed(text)
                    logger.info("Embedding generated for event %s in %.3fs", event.get("event_id"), time.perf_counter() - start_t)
                    metadata = {
                        "video_id": ctx.video_id,
                        "event_id": str(event.get("event_id")),
                        "scene_id": event.get("scene_id"),
                        "start": float(event.get("start", 0.0)),
                        "end": float(event.get("end", 0.0)),
                        "speech": event.get("speech") or "",
                        "vision": event.get("caption") or "",
                    }
                    vector_store.upsert(
                        event_id=f"{ctx.video_id}:{event.get('event_id')}",
                        video_id=ctx.video_id,
                        start=float(event.get("start", 0.0)),
                        end=float(event.get("end", 0.0)),
                        text=text,
                        metadata=metadata,
                        embedding=embedding,
                    )
                ctx.results["vector_db_path"] = vector_store.path
                logger.info("Indexed %d events into ChromaDB at %s", len(events), vector_store.path)

            logger.info("Event building completed: output=%s", out)
        except Exception as e:
            logger.exception("Event building failed for %s: %s", ctx.video_id, e)
            raise
