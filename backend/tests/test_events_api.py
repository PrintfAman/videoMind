import os
import json
from fastapi.testclient import TestClient
from app.main import app


def test_get_events_missing():
    client = TestClient(app)
    resp = client.get("/videos/nonexistent/events")
    assert resp.status_code == 404


def test_get_events_success():
    client = TestClient(app)
    events_dir = os.path.join(os.getcwd(), "data", "events")
    os.makedirs(events_dir, exist_ok=True)
    vid = "evt_api"
    data = {"video_id": vid, "events": [{"event_id": 1, "scene_id": 1, "start": 0.0, "end": 1.0, "duration": 1.0, "speech": "test", "caption": "a", "objects": [], "activities": [], "scene_type": "unknown", "summary": "test"}]}
    path = os.path.join(events_dir, vid + ".json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh)

    resp = client.get(f"/videos/{vid}/events")
    assert resp.status_code == 200
    assert resp.json()["video_id"] == vid
