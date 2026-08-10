from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(prefix="/logging", tags=["logging"])


@router.get("/status")
async def get_logging_status():
    return {
        "logger": "structlog",
        "loki_enabled": settings.LOKI_ENABLED,
        "loki_url": settings.LOKI_URL,
    }
