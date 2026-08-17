from fastapi import APIRouter, HTTPException
from starlette.status import HTTP_404_NOT_FOUND
import os
import json
from app.core.config import get_settings

settings = get_settings()

router = APIRouter(prefix="/videos", tags=["videos"])


@router.get("/{video_id}/transcript")
async def get_transcript(video_id: str):
    transcript_path = os.path.join(os.getcwd(), "data", "transcripts", video_id + ".json")
    if not os.path.exists(transcript_path):
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Transcript not found")
    with open(transcript_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data



@router.get("/{video_id}/scenes")
async def get_scenes(video_id: str):
    scenes_dir = os.path.abspath(os.path.join(os.getcwd(), getattr(settings, "scenes_dir", "data/scenes")))
    scenes_path = os.path.join(scenes_dir, video_id + ".json")
    if not os.path.exists(scenes_path):
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Scenes not found")
    with open(scenes_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data



@router.get("/{video_id}/vision")
async def get_vision(video_id: str):
    vision_dir = os.path.abspath(os.path.join(os.getcwd(), getattr(settings, "vision_output_dir", "data/vision")))
    vision_path = os.path.join(vision_dir, video_id + ".json")
    if not os.path.exists(vision_path):
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Vision analysis not found")
    with open(vision_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data



@router.get("/{video_id}/events")
async def get_events(video_id: str):
    events_dir = os.path.abspath(os.path.join(os.getcwd(), getattr(settings, "events_dir", "data/events")))
    events_path = os.path.join(events_dir, video_id + ".json")
    if not os.path.exists(events_path):
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Events not found")
    with open(events_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data
