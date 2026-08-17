import logging
import time
from app.core.config import get_settings
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore

logger = logging.getLogger("videomind.retrieval")


class RetrievalService:
    def __init__(self, vector_store: VectorStore | None = None, embedding_service: EmbeddingService | None = None):
        settings = get_settings()
        self.vector_store = vector_store or VectorStore(path=getattr(settings, "vector_db_path", "data/vector_db"))
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store.create_collection()

    def search(self, query: str, k: int = 5):
        if not query or not str(query).strip():
            return []
        start = time.perf_counter()
        query_embedding = self.embedding_service.embed(query)
        results = self.vector_store.search(query_embedding, n_results=max(1, int(k)))
        for item in results:
            item["score"] = round(float(item.get("score", 0.0)), 4)
            item["video"] = item.get("metadata", {}).get("video_id")
            item["event_id"] = item.get("metadata", {}).get("event_id")
            item["start"] = item.get("metadata", {}).get("start")
            item["end"] = item.get("metadata", {}).get("end")
            item["speech"] = item.get("metadata", {}).get("speech", "")
            item["vision"] = item.get("metadata", {}).get("vision", "")
            item["scene"] = item.get("metadata", {}).get("scene_id")
        elapsed = time.perf_counter() - start
        logger.info("Retrieval latency %.4fs for query=%s results=%d", elapsed, query, len(results))
        return results
