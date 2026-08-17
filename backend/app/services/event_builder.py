import os
import json
import logging
from typing import List, Dict, Any
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger("videomind.event_builder")


class EventBuilder:
    """Build structured events by fusing scenes, transcripts, and vision outputs."""

    def __init__(self):
        self.events_dir = getattr(settings, "events_dir", "data/events")

    def _read_json(self, path: str) -> Any:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    def build_for_video(self, video_id: str, transcripts_dir: str = None, scenes_dir: str = None, vision_dir: str = None) -> str:
        transcripts_dir = transcripts_dir or getattr(settings, "transcripts_dir", "data/transcripts")
        scenes_dir = scenes_dir or getattr(settings, "scenes_dir", "data/scenes")
        vision_dir = vision_dir or getattr(settings, "vision_output_dir", "data/vision")

        transcript_path = os.path.join(transcripts_dir, video_id + ".json")
        scenes_path = os.path.join(scenes_dir, video_id + ".json")
        vision_path = os.path.join(vision_dir, video_id + ".json")

        if not os.path.exists(transcript_path):
            raise FileNotFoundError(f"Transcript not found: {transcript_path}")
        if not os.path.exists(scenes_path):
            raise FileNotFoundError(f"Scenes not found: {scenes_path}")

        transcript = self._read_json(transcript_path)
        scenes = self._read_json(scenes_path)
        vision = self._read_json(vision_path) if os.path.exists(vision_path) else {"scenes": []}

        segments = transcript.get("segments", [])

        events: List[Dict[str, Any]] = []
        min_dur = getattr(settings, "minimum_event_duration", 0.5)
        max_dur = getattr(settings, "maximum_event_duration", 600.0)

        def speech_for_scene(start: float, end: float) -> str:
            parts = []
            for seg in segments:
                s = float(seg.get("start", 0))
                e = float(seg.get("end", 0))
                if e > start and s < end:
                    parts.append(seg.get("text", "").strip())
            return " ".join([p for p in parts if p])

        vision_map = {s.get("scene_id"): s for s in vision.get("scenes", [])}
        scene_list = scenes.get("scenes", []) if isinstance(scenes, dict) else []

        def add_event(scene_id: Any, start: float, end: float, caption: str, objects: List[str], activities: List[str], scene_type: str, confidence: Any, speech: str):
            duration = max(end - start, 0.0)
            if duration < min_dur:
                logger.debug("Scene %s duration %.3f below min %.3f", scene_id, duration, min_dur)
            if duration > max_dur:
                logger.debug("Scene %s duration %.3f exceeds max %.3f - trimming", scene_id, duration, max_dur)
                end = start + max_dur
                duration = max_dur

            event = {
                "event_id": len(events) + 1,
                "scene_id": scene_id,
                "start": float(start),
                "end": float(end),
                "duration": float(duration),
                "speech": speech,
                "caption": caption,
                "objects": objects,
                "activities": activities,
                "scene_type": scene_type,
                "confidence": confidence,
                "summary": (speech[:200] or caption[:200]) if (speech or caption) else "",
            }
            events.append(event)

        for i, s in enumerate(scene_list, start=1):
            scene_id = s.get("scene_id")
            start = float(s.get("start", 0.0))
            end = float(s.get("end", start))
            caption = ""
            objects = []
            activities = []
            scene_type = "unknown"
            confidence = None
            v = vision_map.get(scene_id)
            if v:
                caption = v.get("caption") or ""
                objects = v.get("objects", []) or []
                activities = v.get("activities", []) or []
                scene_type = v.get("scene_type", "unknown")
                confidence = v.get("confidence")

            speech = speech_for_scene(start, end)
            add_event(scene_id, start, end, caption, objects, activities, scene_type, confidence, speech)

        if not events and segments:
            for idx, seg in enumerate(segments, start=1):
                start = float(seg.get("start", 0.0))
                end = float(seg.get("end", start))
                text = (seg.get("text") or "").strip()
                if not text:
                    continue
                add_event(
                    scene_id=f"segment_{idx}",
                    start=start,
                    end=end,
                    caption="",
                    objects=[],
                    activities=[],
                    scene_type="transcript",
                    confidence=None,
                    speech=text,
                )

        # persist events
        os.makedirs(self.events_dir, exist_ok=True)
        out_path = os.path.join(self.events_dir, video_id + ".json")
        payload = {"video_id": video_id, "events": events}
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)

        logger.info("EventBuilder: built %d events for %s -> %s", len(events), video_id, out_path)
        return out_path


def build_events_for_video(video_id: str) -> str:
    eb = EventBuilder()
    return eb.build_for_video(video_id)
