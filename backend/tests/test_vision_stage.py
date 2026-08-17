import os
import json
from app.services.stages import VisionStage


def test_vision_stage_monkeypatched(tmp_path, monkeypatch):
    # create fake analyzer
    class FakeVR:
        def __init__(self, caption):
            self.caption = caption
            self.objects = ["person"]
            self.activities = ["talking"]
            self.scene_type = "lecture"
            self.confidence = 0.9

    class FakeAnalyzer:
        def analyze(self, image_path, max_size=None):
            return FakeVR("Professor explaining")

    # fake ctx with keyframes
    ctx = type("C", (), {})()
    ctx.video_id = "vid_test"
    # prepare keyframes dir and files
    kdir = os.path.join(os.getcwd(), "data", "keyframes")
    os.makedirs(kdir, exist_ok=True)
    k1 = os.path.join(kdir, "vid_test_scene001.jpg")
    open(k1, "wb").close()
    ctx.results = {"keyframes": [k1]}

    monkeypatch.setattr("app.services.vision.get_vision_analyzer", lambda: FakeAnalyzer())

    stage = VisionStage()
    stage.execute(ctx)

    vision_dir = os.path.join(os.getcwd(), "data", "vision")
    out = os.path.join(vision_dir, "vid_test.json")
    assert os.path.exists(out)
    with open(out, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    assert data["video_id"] == "vid_test"
    assert len(data["scenes"]) == 1
    assert data["scenes"][0]["scene_type"] == "lecture"
