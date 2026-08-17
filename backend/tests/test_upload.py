import io
import os
import json
from fastapi.testclient import TestClient

from app.main import app


def test_upload_video_success(tmp_path, monkeypatch):
    client = TestClient(app)

    # Prepare a small dummy video file
    data = b"\x00\x00dummyvideo"
    file_obj = io.BytesIO(data)
    file_obj.name = "sample.mp4"

    # Monkeypatch media and whisper handlers to avoid needing binaries and real models
    def fake_ffprobe(path: str):
        return {"format": {"filename": os.path.basename(path), "duration": "0.1"}}

    def fake_extract_audio(inp, out):
        # touch the output file
        open(out, "wb").close()

    def fake_transcribe(audio_path, language=None):
        return {
            "text": "hello world",
            "language": "en",
            "segments": [{"start": 0.0, "end": 0.5, "text": "hello world"}],
        }

    monkeypatch.setattr("app.services.media.ffprobe_metadata", fake_ffprobe)
    monkeypatch.setattr("app.services.media.extract_audio", fake_extract_audio)
    monkeypatch.setattr("app.services.whisper_service.transcribe_audio", fake_transcribe)

    files = {"file": ("sample.mp4", file_obj, "video/mp4")}
    resp = client.post("/upload/video", files=files)
    assert resp.status_code == 201
    body = resp.json()
    assert "filename" in body

    saved_name = body["filename"]
    saved_path = os.path.join(os.getcwd(), "data", "videos", saved_name)
    assert os.path.exists(saved_path)

    meta_path = os.path.join(os.getcwd(), "data", "metadata", saved_name + ".json")
    assert os.path.exists(meta_path)
    with open(meta_path, "r", encoding="utf-8") as fh:
        meta = json.load(fh)
    assert meta.get("format")
