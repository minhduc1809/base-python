from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_mongo_db


class CronManagerModel:
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self.db = db or get_mongo_db()
        self.collection = self.db["cron_jobs"]

    async def add_cron_job(self, name: str, cron_expression: str, target_url: str) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        doc = {
            "name": name,
            "cron_expression": cron_expression,
            "target_url": target_url,
            "enabled": True,
            "created_at": now,
            "updated_at": now,
        }
        res = await self.collection.insert_one(doc)
        doc["_id"] = str(res.inserted_id)
        return doc

    async def delete_cron_job(self, job_id: str) -> bool:
        from bson import ObjectId
        try:
            query = {"_id": ObjectId(job_id)}
        except Exception:
            query = {"_id": job_id}

        res = await self.collection.delete_one(query)
        return res.deleted_count > 0

    async def list_cron_jobs(self) -> List[Dict[str, Any]]:
        cursor = self.collection.find({}).sort("created_at", -1)
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results

    async def toggle_cron_job(self, job_id: str, enabled: bool) -> Optional[Dict[str, Any]]:
        from bson import ObjectId
        try:
            query = {"_id": ObjectId(job_id)}
        except Exception:
            query = {"_id": job_id}

        res = await self.collection.find_one_and_update(
            query,
            {"$set": {"enabled": enabled, "updated_at": datetime.now(timezone.utc)}},
            return_document=True,
        )
        if res:
            res["_id"] = str(res["_id"])
        return res
