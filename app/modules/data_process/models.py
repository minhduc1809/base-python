from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_mongo_db


class DataProcessModel:
    """Model quản lý các tiến trình xử lý dữ liệu hàng loạt."""

    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self.db = db or get_mongo_db()
        self.collection = self.db["data_processes"]

    async def create_process(self, name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        doc = {
            "name": name,
            "status": "PENDING",  # PENDING, RUNNING, COMPLETED, FAILED
            "payload": payload,
            "progress": 0.0,
            "created_at": now,
            "updated_at": now,
        }
        res = await self.collection.insert_one(doc)
        doc["_id"] = str(res.inserted_id)
        return doc

    async def get_by_id(self, process_id: str) -> Optional[Dict[str, Any]]:
        from bson import ObjectId
        try:
            query = {"_id": ObjectId(process_id)}
        except Exception:
            query = {"_id": process_id}

        doc = await self.collection.find_one(query)
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc

    async def update_progress(self, process_id: str, status: str, progress: float) -> Optional[Dict[str, Any]]:
        from bson import ObjectId
        try:
            query = {"_id": ObjectId(process_id)}
        except Exception:
            query = {"_id": process_id}

        res = await self.collection.find_one_and_update(
            query,
            {"$set": {"status": status, "progress": progress, "updated_at": datetime.now(timezone.utc)}},
            return_document=True,
        )
        if res:
            res["_id"] = str(res["_id"])
        return res

    async def aggregate_status(self) -> List[Dict[str, Any]]:
        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        cursor = self.collection.aggregate(pipeline)
        results = []
        async for doc in cursor:
            results.append(doc)
        return results
