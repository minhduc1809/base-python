from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db_session, redis_client, mongo_db

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", status_code=status.HTTP_200_OK)
@router.get("/live", status_code=status.HTTP_200_OK)
async def check_liveness():
    """Liveness probe: kiểm tra server có đang chạy hay không."""
    return {"status": "ok", "info": {}, "error": {}, "details": {}}


@router.get("/ready", status_code=status.HTTP_200_OK)
async def check_readiness(db: AsyncSession = Depends(get_db_session)):
    """Readiness probe: kiểm tra server có sẵn sàng nhận traffic hay không."""
    db_status = "up"
    redis_status = "up"
    mongo_status = "up"

    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "down"

    try:
        await redis_client.ping()
    except Exception:
        redis_status = "down"

    try:
        await mongo_db.command("ping")
    except Exception:
        mongo_status = "down"

    is_ready = db_status == "up" and redis_status == "up" and mongo_status == "up"
    status_str = "ok" if is_ready else "error"

    details = {
        "database": {"status": db_status},
        "mongodb": {"status": mongo_status},
        "redis": {"status": redis_status},
    }

    return {
        "status": status_str,
        "info": details,
        "error": {},
        "details": details,
    }
