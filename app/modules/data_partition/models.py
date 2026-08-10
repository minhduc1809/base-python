from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_mongo_db


class DataPartitionModel:
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self.db = db or get_mongo_db()
        self.partitions = self.db["data_partitions"]
        self.dp_users = self.db["data_partition_users"]

    async def get_by_code(self, ma: str) -> Optional[Dict[str, Any]]:
        return await self.partitions.find_one({"ma": ma})

    async def list_all(self, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        cursor = self.partitions.find(query or {})
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results

    async def create_partition(self, ma: str, ten: str, parent_code: Optional[str] = None) -> Dict[str, Any]:
        doc = {
            "ma": ma,
            "ten": ten,
            "parentCode": parent_code,
            "createdAt": datetime.now(timezone.utc),
        }
        res = await self.partitions.insert_one(doc)
        doc["_id"] = str(res.inserted_id)
        return doc
