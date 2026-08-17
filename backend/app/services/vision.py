import os
import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger("videomind.vision")


@dataclass
class VisionResult:
    caption: str
    objects: List[str]
    activities: List[str]
    scene_type: str
    confidence: Optional[float] = None
    extras: Dict[str, Any] = None


class VisionAnalyzer:
    """Abstract Vision Analyzer interface."""

    def analyze(self, image_path: str, max_size: Optional[int] = None) -> VisionResult:
        raise NotImplementedError()


class DummyVisionAnalyzer(VisionAnalyzer):
    def __init__(self):
        logger.info("Using DummyVisionAnalyzer (no model)")

    def analyze(self, image_path: str, max_size: Optional[int] = None) -> VisionResult:
        # Very lightweight placeholder implementation
        base = os.path.basename(image_path)
        caption = f"Image of {base}"
        return VisionResult(caption=caption, objects=[], activities=[], scene_type="unknown", confidence=0.0, extras={})


class BLIPVisionAnalyzer(VisionAnalyzer):
    def __init__(self, model_name: str = "Salesforce/blip-image-captioning-base", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self._pipe = None
        logger.info("BLIPVisionAnalyzer configured model=%s device=%s", model_name, device)

    def _load(self):
        if self._pipe is not None:
            return
        try:
            from transformers import pipeline
            from PIL import Image
        except Exception as e:
            logger.error("Failed to import transformers/PIL for BLIP analyzer: %s", e)
            raise
        logger.info("Loading BLIP model %s", self.model_name)
        # device_map: -1 for CPU
        device = -1
        try:
            self._pipe = pipeline("image-to-text", model=self.model_name, device=device)
        except Exception:
            # fallback: try without specifying device
            self._pipe = pipeline("image-to-text", model=self.model_name)

    def analyze(self, image_path: str, max_size: Optional[int] = None) -> VisionResult:
        self._load()
        from PIL import Image
        img = Image.open(image_path).convert("RGB")
        if max_size:
            img.thumbnail((max_size, max_size))
        outputs = self._pipe(img)
        # pipeline returns a list of dicts with 'generated_text'
        caption = outputs[0].get("generated_text") if outputs else ""
        return VisionResult(caption=caption or "", objects=[], activities=[], scene_type="unknown", confidence=None, extras={"raw": outputs})


_ANALYZER_INSTANCE: Optional[VisionAnalyzer] = None


def get_vision_analyzer() -> VisionAnalyzer:
    global _ANALYZER_INSTANCE
    if _ANALYZER_INSTANCE is not None:
        return _ANALYZER_INSTANCE

    model = getattr(settings, "vision_model", "dummy")
    device = getattr(settings, "inference_device", "cpu")
    if model is None or model == "dummy":
        _ANALYZER_INSTANCE = DummyVisionAnalyzer()
    else:
        try:
            _ANALYZER_INSTANCE = BLIPVisionAnalyzer(model_name=model, device=device)
        except Exception:
            logger.exception("Failed to initialize BLIPVisionAnalyzer, falling back to DummyVisionAnalyzer")
            _ANALYZER_INSTANCE = DummyVisionAnalyzer()
    return _ANALYZER_INSTANCE
