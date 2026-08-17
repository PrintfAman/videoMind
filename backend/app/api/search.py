import logging

from fastapi import APIRouter, HTTPException

from app.schemas.search import SearchRequest
from app.services.retrieval import RetrievalService

logger = logging.getLogger("videomind.search_api")
router = APIRouter(tags=["search"])
retrieval_service = RetrievalService()


@router.post("/search")
async def search_events(payload: SearchRequest):
    try:
        results = retrieval_service.search(payload.query, k=payload.top_k)
        return [
            {
                "score": item.get("score", 0.0),
                "video": item.get("video"),
                "event_id": item.get("event_id"),
                "start": item.get("start"),
                "end": item.get("end"),
                "speech": item.get("speech", ""),
                "vision": item.get("vision", ""),
            }
            for item in results
        ]
    except Exception as exc:  # pragma: no cover
        logger.exception("Search failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
