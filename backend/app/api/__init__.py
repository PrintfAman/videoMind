"""API package for routers."""

from fastapi import APIRouter

from app.api.search import router as search_router
from app.api.uploads import router as uploads_router
from app.api.videos import router as videos_router

router = APIRouter()
router.include_router(uploads_router)
router.include_router(videos_router)
router.include_router(search_router)


