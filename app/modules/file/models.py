from datetime import datetime, timezone
from typing import Any, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_mongo_db


class FileModel:
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self.db = db or get_mongo_db()
        self.collection = self.db["files"]

    async def save_file_meta(
        self, filename: str, object_name: str, size: int, content_type: str, user_id: str
    ) -> Dict[str, Any]:
        doc = {
            "filename": filename,
            "objectName": object_name,
            "size": size,
            "contentType": content_type,
            "uploadedBy": str(user_id),
            "createdAt": datetime.now(timezone.utc),
        }
        res = await self.collection.insert_one(doc)
        doc["_id"] = str(res.inserted_id)
        return doc

    async def get_by_id(self, file_id: str) -> Optional[Dict[str, Any]]:
        from bson import ObjectId

        try:
            return await self.collection.find_one({"_id": ObjectId(file_id)})
        except Exception:
            return await self.collection.find_one({"objectName": file_id})

    async def delete_meta(self, file_id: str) -> bool:
        from bson import ObjectId

        try:
            res = await self.collection.delete_one({"_id": ObjectId(file_id)})
            return res.deleted_count > 0
        except Exception:
            res = await self.collection.delete_one({"objectName": file_id})
            return res.deleted_count > 0
