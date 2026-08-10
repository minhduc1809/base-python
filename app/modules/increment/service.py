from typing import Any, Dict, Optional
from redis.asyncio import Redis
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_redis, get_mongo_db


class IncrementService:
    """Port 1-1 từ IncrementService trong NestJS (increment.service.ts:L10-45)."""

    def __init__(self, redis: Optional[Redis] = None, db: Optional[AsyncIOMotorDatabase] = None):
        self.redis = redis
        self.db = db or get_mongo_db()

    async def _get_redis(self) -> Redis:
        if not self.redis:
            self.redis = await get_redis()
        return self.redis

    async def get_increase_count(self, key_name: str) -> int:
        """Port 1-1 từ getIncreaseCount (increment.service.ts:L14-17)."""
        return await self.get_next_increment(key_name)

    async def get_next_increment(self, key_name: str) -> int:
        """Port từ getNextIncrement (increment.service.ts:L15-25): Lấy số tự tăng tiếp theo (Atomic)."""
        redis = await self._get_redis()
        try:
            return await redis.incr(f"seq:{key_name}")
        except Exception:
            # Fallback MongoDB counters
            coll = self.db["counters"]
            res = await coll.find_one_and_update(
                {"_id": key_name},
                {"$inc": {"seq": 1}},
                upsert=True,
                return_document=True,
            )
            return res.get("seq", 1)

    async def reset_increment(self, key_name: str, value: int = 0) -> bool:
        """Port từ resetIncrement (increment.service.ts:L28-35)."""
        redis = await self._get_redis()
        try:
            await redis.set(f"seq:{key_name}", value)
        except Exception:
            pass

        coll = self.db["counters"]
        await coll.update_one({"_id": key_name}, {"$set": {"seq": value}}, upsert=True)
        return True

    async def get_increment_value(self, key_name: str) -> int:
        """Port từ getIncrementValue (increment.service.ts:L38-45)."""
        redis = await self._get_redis()
        try:
            val = await redis.get(f"seq:{key_name}")
            if val is not None:
                return int(val)
        except Exception:
            pass

        coll = self.db["counters"]
        doc = await coll.find_one({"_id": key_name})
        return doc.get("seq", 0) if doc else 0
