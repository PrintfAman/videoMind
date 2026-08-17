import os
import subprocess
import shutil
from app.services.stages import KeyframeExtractionStage


def test_keyframe_extraction_stage_monkeypatched(tmp_path, monkeypatch):
    # Prepare fake scene data
    ctx = type("C", (), {})()
    ctx.video_path = os.path.join(os.getcwd(), "data", "videos", "dummy.mp4")
    ctx.video_id = "dummy"
    ctx.scene_data = [{"scene_id": 1, "start": 0.0, "end": 2.0}, {"scene_id": 2, "start": 2.0, "end": 4.0}]
    ctx.results = {}

    # Monkeypatch ffmpeg presence and subprocess.run to create expected files
    monkeypatch.setattr(shutil, "which", lambda name: "ffmpeg")

    def fake_run(cmd, capture_output=True, text=True):
        out_path = cmd[-1]
        # create dummy file
        open(out_path, "wb").close()
        class R:
            returncode = 0
            stderr = ""
        return R()

    monkeypatch.setattr(subprocess, "run", fake_run)

    key_stage = KeyframeExtractionStage()
    key_stage.execute(ctx)

    keyframes_dir = os.path.join(os.getcwd(), "data", "keyframes")
    assert os.path.exists(os.path.join(keyframes_dir, "dummy_scene001.jpg"))
    assert os.path.exists(os.path.join(keyframes_dir, "dummy_scene002.jpg"))
