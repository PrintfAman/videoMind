import logging
from typing import Any
from functools import lru_cache

from app.core.config import get_settings

logger = logging.getLogger("videomind.embedding")


class EmbeddingService:
    """Lazy-load and cache a SentenceTransformer model for text embeddings."""

    _instance: "EmbeddingService | None" = None
    _model: Any = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, model_name: str | None = None, device: str | None = None):
        if getattr(self, "_initialized", False):
            return

        settings = get_settings()
        self.model_name = model_name or getattr(settings, "embedding_model", "BAAI/bge-small-en-v1.5")
        self.device = (device or getattr(settings, "device", "cpu") or "cpu").lower()
        self._initialized = True

    def _load_model(self):
        if self._model is not None:
            return self._model

        from sentence_transformers import SentenceTransformer

        model_device = self.device
        if model_device in {"gpu", "cuda", "cuda:0"}:
            model_device = "cuda"
        elif model_device == "mps":
            model_device = "mps"
        else:
            model_device = "cpu"

        logger.info("Loading embedding model %s on %s", self.model_name, model_device)
        self._model = SentenceTransformer(self.model_name, device=model_device)
        logger.info("Embedding model loaded: %s", self.model_name)
        return self._model

    def embed(self, text: str) -> list[float]:
        if text is None:
            raise ValueError("text is required")
        normalized = " ".join(str(text).strip().split())
        if not normalized:
            return []

        model = self._load_model()
        vector = model.encode(normalized, convert_to_numpy=False)
        if hasattr(vector, "tolist"):
            vector = vector.tolist()
        if isinstance(vector, list) and vector and isinstance(vector[0], list):
            vector = vector[0]
        return [float(value) for value in vector]


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
