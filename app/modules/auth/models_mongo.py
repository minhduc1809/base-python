from datetime import datetime, timezone
from typing import Any, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_mongo_db


class AuthSessionService:
    def __init__(self, db: AsyncIOMotorDatabase = None):
        self.db = db or get_mongo_db()
        self.collection = self.db["auth_sessions"]

    async def create_session(
        self,
        user_id: int,
        jti: str,
        exp: int,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        origin: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Tạo và lưu Auth session vào MongoDB."""
        doc = {
            "user_id": user_id,
            "jti": jti,
            "exp": exp,
            "ip": ip,
            "user_agent": user_agent,
            "origin": origin,
            "platform": platform,
            "revoked": False,
            "created_at": datetime.now(timezone.utc),
        }
        res = await self.collection.insert_one(doc)
        doc["_id"] = str(res.inserted_id)
        return doc

    async def get_session(self, jti: str) -> Optional[Dict[str, Any]]:
        """Lấy Auth session theo jti."""
        return await self.collection.find_one({"jti": jti, "revoked": False})

    async def revoke_session(self, jti: str) -> bool:
        """Thu hồi Auth session (Logout)."""
        res = await self.collection.update_one(
            {"jti": jti},
            {"$set": {"revoked": True, "revoked_at": datetime.now(timezone.utc)}},
        )
        return res.modified_count > 0
