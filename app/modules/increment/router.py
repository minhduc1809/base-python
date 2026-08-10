from fastapi import APIRouter, Depends, Query
from redis.asyncio import Redis
from app.core.database import get_redis

router = APIRouter(prefix="/increment", tags=["increment"])


@router.post("/next")
async def get_next_sequence(key: str = Query("default"), redis: Redis = Depends(get_redis)):
    next_val = await redis.incr(f"seq:inc:{key}")
    return {"key": key, "value": next_val}
