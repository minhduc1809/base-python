"""
Topic Service — Port 1-1 từ topic.service.ts (base-backend).
"""
from typing import Any, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.common.exceptions import AppException

MAX_TOPIC_SUBSCRIPTION = 5000


class TopicService:
    """Port 1-1 từ TopicService (topic.service.ts:L12-53)."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.topics_coll = db["topics"]
        self.user_topics_coll = db["user_topics"]

    async def user_subscribe_topic(self, user_id: str, topic_id_or_name: str) -> Dict[str, Any]:
        """Port 1-1 từ userSubscribeTopic(user, subscription).
        Thực hiện đủ 3 bước validate:
        1. Kiểm tra topic tồn tại (topics_coll)
        2. Kiểm tra đã subscribe chưa
        3. Kiểm tra số lượng đã vượt quá MAX_TOPIC_SUBSCRIPTION (5000) không
        """
        # 1. Check topic exist
        topic_doc = None
        try:
            topic_doc = await self.topics_coll.find_one({"_id": ObjectId(topic_id_or_name)})
        except Exception:
            topic_doc = await self.topics_coll.find_one({"name": topic_id_or_name})

        if not topic_doc:
            raise AppException(status_code=404, message="error-topic-not-found", error="Not Found")

        topic_name = topic_doc.get("name", topic_id_or_name)
        topic_id_str = str(topic_doc["_id"])

        # 2. Check exist subscription
        user_topic = await self.user_topics_coll.find_one({"userId": str(user_id)})
        subscriptions = user_topic.get("subscriptions", []) if user_topic else []

        already_subscribed = any(
            s.get("topic") == topic_id_str or s.get("topic") == topic_name for s in subscriptions
        )
        if already_subscribed:
            raise AppException(
                status_code=409,
                message=f"error-topic-subscribed: {topic_name}",
                error="Conflict",
            )

        # 3. Check max subscription limit
        if len(subscriptions) >= MAX_TOPIC_SUBSCRIPTION:
            raise AppException(
                status_code=400,
                message=f"error-topic-subscription-limit-exceed: {MAX_TOPIC_SUBSCRIPTION}",
                error="Bad Request",
            )

        # 4. Create subscription
        from datetime import datetime, timezone
        new_sub = {"topic": topic_id_str, "name": topic_name, "subscribedAt": datetime.now(timezone.utc)}
        res = await self.user_topics_coll.find_one_and_update(
            {"userId": str(user_id)},
            {
                "$push": {"subscriptions": new_sub},
                "$set": {"updatedAt": datetime.now(timezone.utc)},
            },
            upsert=True,
            return_document=True,
        )
        res["_id"] = str(res["_id"])
        return new_sub
