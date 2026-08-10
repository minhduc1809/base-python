from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_redis, get_mongo_db
from app.modules.increment.service import IncrementService

router = APIRouter(prefix="/increment", tags=["increment"])


@router.post("/{key_name}/next")
async def get_next_increment(
    key_name: str,
    redis: Redis = Depends(get_redis),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    service = IncrementService(redis=redis, db=db)
    seq = await service.get_next_increment(key_name)
    return {"key": key_name, "seq": seq}


@router.get("/{key_name}")
async def get_increment_value(
    key_name: str,
    redis: Redis = Depends(get_redis),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    service = IncrementService(redis=redis, db=db)
    seq = await service.get_increment_value(key_name)
    return {"key": key_name, "seq": seq}


@router.put("/{key_name}/reset")
async def reset_increment(
    key_name: str,
    value: int = 0,
    redis: Redis = Depends(get_redis),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    service = IncrementService(redis=redis, db=db)
    await service.reset_increment(key_name, value)
    return {"key": key_name, "seq": value}
