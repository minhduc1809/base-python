from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_mongo_db


class QuyTacMaModel:
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self.db = db or get_mongo_db()
        self.collection = self.db["quy_tac_ma"]

    async def get_by_nguon(self, nguon: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"nguon": nguon})

    async def upsert_quy_tac(self, nguon: str, cau_hinh: List[Dict[str, Any]]) -> Dict[str, Any]:
        res = await self.collection.find_one_and_update(
            {"nguon": nguon},
            {"$set": {"nguon": nguon, "cauHinh": cau_hinh}},
            upsert=True,
            return_document=True,
        )
        return res
