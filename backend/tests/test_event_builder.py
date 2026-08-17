import os
import json
from app.services.event_builder import EventBuilder


def test_event_builder_basic(tmp_path):
    vid = "evt_vid"
    base = os.getcwd()
    # prepare transcript
    tdir = os.path.join(base, "data", "transcripts")
    os.makedirs(tdir, exist_ok=True)
    transcript = {"id": vid, "segments": [{"start": 0.0, "end": 2.0, "text": "Hello world."}, {"start": 2.0, "end": 5.0, "text": "More talk."}]}
    with open(os.path.join(tdir, vid + ".json"), "w", encoding="utf-8") as fh:
        json.dump(transcript, fh)
    # prepare scenes
    sdir = os.path.join(base, "data", "scenes")
    os.makedirs(sdir, exist_ok=True)
    scenes = {"video_id": vid, "scene_count": 1, "scenes": [{"scene_id": 1, "start": 0.0, "end": 5.0}]}
    with open(os.path.join(sdir, vid + ".json"), "w", encoding="utf-8") as fh:
        json.dump(scenes, fh)
    # prepare vision
    vdir = os.path.join(base, "data", "vision")
    os.makedirs(vdir, exist_ok=True)
    vision = {"video_id": vid, "scenes": [{"scene_id": 1, "caption": "A cat on a table", "objects": ["cat"], "activities": ["sitting"], "scene_type": "indoor", "confidence": 0.8}]}
    with open(os.path.join(vdir, vid + ".json"), "w", encoding="utf-8") as fh:
        json.dump(vision, fh)

    eb = EventBuilder()
    out = eb.build_for_video(vid)
    assert os.path.exists(out)
    with open(out, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    assert data["video_id"] == vid
    assert len(data["events"]) == 1
    evt = data["events"][0]
    assert evt["speech"].startswith("Hello world")
    assert evt["caption"] == "A cat on a table"


def test_event_builder_falls_back_to_transcript_segments():
    vid = "evt_transcript_only"
    base = os.getcwd()
    tdir = os.path.join(base, "data", "transcripts")
    os.makedirs(tdir, exist_ok=True)
    transcript = {"id": vid, "segments": [{"start": 0.0, "end": 2.0, "text": "person enters kitchen"}, {"start": 2.0, "end": 4.0, "text": "someone cooks food"}]}
    with open(os.path.join(tdir, vid + ".json"), "w", encoding="utf-8") as fh:
        json.dump(transcript, fh)

    sdir = os.path.join(base, "data", "scenes")
    os.makedirs(sdir, exist_ok=True)
    with open(os.path.join(sdir, vid + ".json"), "w", encoding="utf-8") as fh:
        json.dump({"video_id": vid, "scene_count": 0, "scenes": []}, fh)

    eb = EventBuilder()
    out = eb.build_for_video(vid)
    with open(out, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    assert len(data["events"]) == 2
    assert data["events"][0]["speech"] == "person enters kitchen"
    assert data["events"][1]["summary"] == "someone cooks food"
