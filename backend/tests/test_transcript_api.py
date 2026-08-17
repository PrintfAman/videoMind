import os
import json
from fastapi.testclient import TestClient
from app.main import app


def test_get_transcript_missing(tmp_path):
    client = TestClient(app)
    resp = client.get("/videos/nonexistent/transcript")
    assert resp.status_code == 404


def test_get_transcript_success(tmp_path):
    client = TestClient(app)
    transcripts_dir = os.path.join(os.getcwd(), "data", "transcripts")
    os.makedirs(transcripts_dir, exist_ok=True)
    vid = "sample_video"
    data = {"id": vid, "language": "en", "duration": 1.2, "segments": []}
    path = os.path.join(transcripts_dir, vid + ".json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh)

    resp = client.get(f"/videos/{vid}/transcript")
    assert resp.status_code == 200
    assert resp.json()["id"] == vid
