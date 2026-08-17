from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logger import get_logger
from app.utils.exceptions import register_exception_handlers


settings = get_settings()
logger = get_logger(settings)


app = FastAPI(title=settings.app_name)

# include API routers
from app.api import router as api_router
app.include_router(api_router)

origins = [o.strip() for o in (settings.cors_origins or "").split(",") if o.strip()]
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy"}


register_exception_handlers(app, logger)
