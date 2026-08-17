import os
import json
from fastapi.testclient import TestClient
from app.main import app


def test_get_scenes_missing():
    client = TestClient(app)
    resp = client.get("/videos/nonexistent/scenes")
    assert resp.status_code == 404


def test_get_scenes_success():
    client = TestClient(app)
    scenes_dir = os.path.join(os.getcwd(), "data", "scenes")
    os.makedirs(scenes_dir, exist_ok=True)
    vid = "vid123"
    data = {"video_id": vid, "scene_count": 2, "scenes": [{"scene_id": 1, "start": 0.0, "end": 1.0, "keyframe": "vid123_scene001.jpg"}]}
    path = os.path.join(scenes_dir, vid + ".json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh)

    resp = client.get(f"/videos/{vid}/scenes")
    assert resp.status_code == 200
    assert resp.json()["video_id"] == vid
