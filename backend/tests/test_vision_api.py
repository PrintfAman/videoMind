import os
import json
from fastapi.testclient import TestClient
from app.main import app


def test_get_vision_missing():
    client = TestClient(app)
    resp = client.get("/videos/nonexistent/vision")
    assert resp.status_code == 404


def test_get_vision_success():
    client = TestClient(app)
    vision_dir = os.path.join(os.getcwd(), "data", "vision")
    os.makedirs(vision_dir, exist_ok=True)
    vid = "vid_api"
    data = {"video_id": vid, "scenes": [{"scene_id": 1, "caption": "A test", "objects": [], "activities": [], "scene_type": "unknown"}]}
    path = os.path.join(vision_dir, vid + ".json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh)

    resp = client.get(f"/videos/{vid}/vision")
    assert resp.status_code == 200
    assert resp.json()["video_id"] == vid
