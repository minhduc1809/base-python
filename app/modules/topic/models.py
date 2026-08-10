from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_mongo_db


class UserTopicModel:
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self.db = db or get_mongo_db()
        self.collection = self.db["user_topics"]

    async def subscribe(self, user_id: str, topic_name: str) -> Dict[str, Any]:
        doc = await self.collection.find_one_and_update(
            {"user": str(user_id)},
            {
                "$addToSet": {"subscriptions": {"topic": topic_name, "subscribedAt": datetime.now(timezone.utc)}},
                "$set": {"updatedAt": datetime.now(timezone.utc)},
            },
            upsert=True,
            return_document=True,
        )
        doc["_id"] = str(doc["_id"])
        return doc

    async def unsubscribe(self, user_id: str, topic_name: str) -> bool:
        res = await self.collection.update_one(
            {"user": str(user_id)},
            {"$pull": {"subscriptions": {"topic": topic_name}}},
        )
        return res.modified_count > 0
