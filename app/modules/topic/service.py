from typing import Any, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.common.exceptions import AppException

MAX_TOPIC_SUBSCRIPTION = 5000


class TopicService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.topics_coll = db["topics"]
        self.user_topics_coll = db["user_topics"]

    async def user_subscribe_topic(self, user_id: str, topic_id_or_name: str) -> Dict[str, Any]:
        """Thực hiện đủ 3 bước validate:
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
        existing_sub = await self.user_topics_coll.find_one({"user_id": user_id, "topic_name": topic_name})
        if existing_sub:
            return {
                "message": "User already subscribed to topic",
                "topic": topic_name,
                "subscribed": True,
            }

        # 3. Check max subscription limit
        user_sub_count = await self.user_topics_coll.count_documents({"user_id": user_id})
        if user_sub_count >= MAX_TOPIC_SUBSCRIPTION:
            raise AppException(
                status_code=400,
                message=f"Maximum topic subscription limit ({MAX_TOPIC_SUBSCRIPTION}) reached",
                error="Bad Request",
            )

        # 4. Create subscription
        sub_doc = {
            "user_id": user_id,
            "topic_id": topic_id_str,
            "topic_name": topic_name,
        }
        res = await self.user_topics_coll.insert_one(sub_doc)
        sub_doc["_id"] = str(res.inserted_id)

        return {
            "message": "Successfully subscribed to topic",
            "subscription": sub_doc,
        }
