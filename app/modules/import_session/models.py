from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_mongo_db


class ImportSessionModel:
    """Port 1-1 từ ImportSession entity (entities/import-session.entity.ts)."""

    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self.db = db or get_mongo_db()
        self.collection = self.db["import_sessions"]

    async def create_session(self, module_name: str, total_records: int = 0) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        doc = {
            "module_name": module_name,
            "status": "PROCESSING",  # PROCESSING, COMPLETED, FAILED
            "total_records": total_records,
            "processed_records": 0,
            "error_count": 0,
            "error_logs": [],
            "created_at": now,
            "updated_at": now,
        }
        res = await self.collection.insert_one(doc)
        doc["_id"] = str(res.inserted_id)
        return doc

    async def get_by_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        from bson import ObjectId
        try:
            query = {"_id": ObjectId(session_id)}
        except Exception:
            query = {"_id": session_id}

        doc = await self.collection.find_one(query)
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc

    async def update_status(
        self, session_id: str, status: str, processed: int = 0, error_logs: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        from bson import ObjectId
        try:
            query = {"_id": ObjectId(session_id)}
        except Exception:
            query = {"_id": session_id}

        update_dict = {
            "status": status,
            "processed_records": processed,
            "updated_at": datetime.now(timezone.utc),
        }
        if error_logs is not None:
            update_dict["error_logs"] = error_logs
            update_dict["error_count"] = len(error_logs)

        res = await self.collection.find_one_and_update(
            query, {"$set": update_dict}, return_document=True
        )
        if res:
            res["_id"] = str(res["_id"])
        return res
