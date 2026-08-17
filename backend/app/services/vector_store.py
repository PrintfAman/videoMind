import os
import json
import logging
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger("videomind.vector_store")


class VectorStore:
    """Simple ChromaDB-backed vector store for video events."""

    def __init__(self, path: str | None = None, collection_name: str = "video_events"):
        settings = get_settings()
        self.path = path or getattr(settings, "vector_db_path", "data/vector_db")
        self.collection_name = collection_name
        self._collection = None
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            import chromadb
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("ChromaDB is required for semantic search") from exc

        self._client = chromadb.PersistentClient(path=self.path)
        return self._client

    def create_collection(self):
        client = self._get_client()
        collection = client.get_or_create_collection(name=self.collection_name)
        self._collection = collection
        return collection

    def _ensure_collection(self):
        if self._collection is None:
            self._collection = self.create_collection()
        return self._collection

    def upsert(
        self,
        event_id: str,
        video_id: str,
        start: float,
        end: float,
        text: str,
        metadata: dict[str, Any] | None = None,
        embedding: list[float] | None = None,
    ) -> bool:
        collection = self._ensure_collection()
        record_metadata = dict(metadata or {})
        record_metadata.update({
            "video_id": video_id,
            "event_id": str(event_id),
            "start": float(start),
            "end": float(end),
        })

        if embedding is None:
            embedding = []

        start_t = __import__("time").perf_counter()
        collection.upsert(
            ids=[str(event_id)],
            embeddings=[embedding],
            metadatas=[record_metadata],
            documents=[text or ""],
        )
        logger.info("Vector insertion completed for event_id=%s in %.3fs", event_id, __import__("time").perf_counter() - start_t)
        return True

    def search(self, query_embedding: list[float], n_results: int = 5):
        collection = self._ensure_collection()
        if not query_embedding:
            return []
        results = collection.query(query_embeddings=[query_embedding], n_results=n_results)
        items = []
        for idx, doc_id in enumerate(results.get("ids", [[]])[0]):
            metadata = results.get("metadatas", [[]])[0][idx]
            distance = results.get("distances", [[]])[0][idx] if "distances" in results else None
            items.append({
                "id": doc_id,
                "score": 1.0 - distance if distance is not None else 0.0,
                "document": results.get("documents", [[]])[0][idx],
                "metadata": metadata,
            })
        return items

    def delete(self, event_id: str) -> bool:
        collection = self._ensure_collection()
        collection.delete(ids=[str(event_id)])
        return True

    def count(self) -> int:
        collection = self._ensure_collection()
        return int(collection.count())
