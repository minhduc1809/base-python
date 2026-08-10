from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(prefix="/core", tags=["core"])


@router.get("/info")
async def get_core_info():
    return {
        "app_name": "AISoft Backend Python",
        "env": settings.SERVER_ENV,
        "address": settings.SERVER_ADDRESS,
        "timezone": settings.SERVER_TIMEZONE,
    }
