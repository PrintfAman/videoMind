import sys
import types
import os
import json
from app.services.stages import SceneDetectionStage


def test_scene_detection_stage_modern_api(tmp_path, monkeypatch):
    fake = types.ModuleType("scenedetect")

    class FakeTimecode:
        def __init__(self, s):
            self._s = s

        def get_seconds(self):
            return self._s

        def get_timecode(self):
            return str(self._s)

    class VideoStream:
        def __init__(self, path):
            self.path = path

    class SceneManager:
        def __init__(self):
            self._scenes = [(FakeTimecode(0.0), FakeTimecode(1.5)), (FakeTimecode(1.5), FakeTimecode(3.0))]

        def add_detector(self, d):
            pass

        def detect_scenes(self, video=None, frame_source=None, **kwargs):
            pass

        def get_scene_list(self):
            return self._scenes

    class ContentDetector:
        def __init__(self, threshold=30.0, **kwargs):
            pass

    fake.VideoStream = VideoStream
    fake.SceneManager = SceneManager
    fake.open_video = lambda path: VideoStream(path)

    detectors_module = types.ModuleType("scenedetect.detectors")
    detectors_module.ContentDetector = ContentDetector
    fake.detectors = detectors_module

    monkeypatch.setitem(sys.modules, "scenedetect", fake)
    monkeypatch.setitem(sys.modules, "scenedetect.detectors", detectors_module)

    class Ctx:
        pass

    ctx = type("C", (), {})()
    ctx.video_path = os.path.join(os.getcwd(), "data", "videos", "dummy.mp4")
    ctx.video_id = "dummy_modern"
    ctx.results = {}
    stage = SceneDetectionStage()
    scenes_dir = os.path.join(os.getcwd(), "data", "scenes")
    os.makedirs(scenes_dir, exist_ok=True)
    stage.execute(ctx)

    summary_path = os.path.join(scenes_dir, ctx.video_id + ".json")
    assert os.path.exists(summary_path)
    with open(summary_path, "r", encoding="utf-8") as fh:
        summary = json.load(fh)
    assert summary["video_id"] == ctx.video_id
    assert summary["scene_count"] == 2


def test_scene_detection_stage_monkeypatched(tmp_path, monkeypatch):
    # Create fake scenedetect module
    fake = types.ModuleType("scenedetect")

    class FakeTimecode:
        def __init__(self, s):
            self._s = s

        def get_seconds(self):
            return self._s

        def get_timecode(self):
            return str(self._s)

    class VideoManager:
        def __init__(self, args):
            pass

        def start(self):
            pass

    class SceneManager:
        def __init__(self):
            self._scenes = [(FakeTimecode(0.0), FakeTimecode(1.5)), (FakeTimecode(1.5), FakeTimecode(3.0))]

        def add_detector(self, d):
            pass

        def detect_scenes(self, frame_source=None):
            pass

        def get_scene_list(self):
            return self._scenes

    class ContentDetector:
        def __init__(self, threshold=30.0):
            pass

    fake.VideoManager = VideoManager
    fake.SceneManager = SceneManager
    detectors_module = types.ModuleType("scenedetect.detectors")
    detectors_module.ContentDetector = ContentDetector
    fake.detectors = detectors_module
    import sys
    sys.modules["scenedetect.detectors"] = detectors_module

    sys.modules["scenedetect"] = fake

    # prepare context
    class Ctx:
        pass

    ctx = type("C", (), {})()
    ctx.video_path = os.path.join(os.getcwd(), "data", "videos", "dummy.mp4")
    ctx.video_id = "dummy"
    ctx.results = {}
    stage = SceneDetectionStage()
    # ensure scenes dir exists
    scenes_dir = os.path.join(os.getcwd(), "data", "scenes")
    os.makedirs(scenes_dir, exist_ok=True)
    stage.execute(ctx)
    # check summary written
    summary_path = os.path.join(scenes_dir, ctx.video_id + ".json")
    assert os.path.exists(summary_path)
    with open(summary_path, "r", encoding="utf-8") as fh:
        summary = json.load(fh)
    assert summary["video_id"] == ctx.video_id
    assert summary["scene_count"] == 2
