from fastapi import APIRouter, UploadFile, File, HTTPException
from starlette.responses import JSONResponse
from starlette.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
import os

from app.core.config import get_settings
from app.core.logger import get_logger
from app.services.storage import save_uploaded_file
from app.services.orchestrator import process_video
from app.utils.files import validate_video_upload

router = APIRouter(prefix="/upload", tags=["upload"])
settings = get_settings()
logger = get_logger(settings)


@router.post("/video", status_code=HTTP_201_CREATED)
async def upload_video(file: UploadFile = File(...)) -> JSONResponse:
    logger.info("Upload received: filename=%s content_type=%s", file.filename, file.content_type)

    # Validate
    try:
        validate_video_upload(file)
    except ValueError as e:
        logger.warning("Validation failed for %s: %s", file.filename, e)
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(e))

    # Save file
    saved_path = save_uploaded_file(file, dest_dir=os.path.join(os.getcwd(), "data", "videos"))
    logger.info("Saved uploaded video to %s", saved_path)

    # Hand off to orchestrator (processing moved out of endpoint)
    try:
        results = process_video(saved_path)
        logger.info("Processing completed for %s: %s", saved_path, results)
    except Exception as e:
        logger.exception("Processing failed for %s: %s", saved_path, e)

    return JSONResponse(status_code=HTTP_201_CREATED, content={"filename": os.path.basename(saved_path)})
