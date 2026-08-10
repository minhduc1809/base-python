from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from app.core.database import get_redis

router = APIRouter(prefix="/redis", tags=["redis"])


@router.get("/ping")
async def ping_redis(redis: Redis = Depends(get_redis)):
    res = await redis.ping()
    return {"status": "ok" if res else "error", "response": res}
