from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_mongo_db


class NotificationModel:
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self.db = db or get_mongo_db()
        self.collection = self.db["notifications"]

    async def create_notification(
        self,
        title: str,
        content: str,
        receiver_type: str,
        sender_id: str,
        sender_name: str,
        users: Optional[List[str]] = None,
        topics: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        doc = {
            "title": title,
            "content": content,
            "receiverType": receiver_type,
            "sender": sender_id,
            "senderName": sender_name,
            "users": users or [],
            "topics": topics or [],
            "createdAt": datetime.now(timezone.utc),
        }
        res = await self.collection.insert_one(doc)
        doc["_id"] = str(res.inserted_id)
        return doc
