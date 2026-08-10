"""
Auth Session MongoDB model.
Collection 'auth_sessions' quản lý các phiên làm việc của người dùng.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_mongo_db


class AuthSessionService:
    """Service thao tác lưu trữ Auth Session trong MongoDB."""

    def __init__(self, db: AsyncIOMotorDatabase = None):
        self.db = db or get_mongo_db()
        self.collection = self.db["auth_sessions"]

    # ─── create (auth.service.ts:L86 → authRepository.create(doc)) ───
    async def create_session(
        self,
        user_id: int,
        jti: str,
        exp: Optional[int] = None,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        origin: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Tạo auth session — tương đương authRepository.create(doc)."""
        doc = {
            "user": user_id,
            "jti": jti,
            "exp": exp,
            "ip": ip,
            "userAgent": user_agent,
            "origin": origin,
            "platform": platform,
            "createdAt": datetime.now(timezone.utc),
        }
        res = await self.collection.insert_one(doc)
        doc["_id"] = str(res.inserted_id)
        return doc

    # ─── getOne({_id, jti}) — auth.service.ts:L150-153 ──────────────
    async def get_session_by_id_and_jti(self, auth_id: str, jti: str) -> Optional[Dict[str, Any]]:
        """Port 1-1 từ authRepository.getOne({_id: payload.auth, jti: payload.jti})."""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(auth_id), "jti": jti})
            if doc:
                doc["_id"] = str(doc["_id"])
            return doc
        except Exception:
            return None

    # ─── updateById (auth.service.ts:L99) ────────────────────────────
    async def update_session(self, auth_id: str, update: dict) -> bool:
        """Port 1-1 từ authRepository.updateById(auth._id, auth)."""
        try:
            res = await self.collection.update_one(
                {"_id": ObjectId(auth_id)},
                {"$set": update},
            )
            return res.modified_count > 0
        except Exception:
            return False

    # ─── deleteOne({_id, jti}) — auth.service.ts:L186-189 ───────────
    async def delete_session(self, auth_id: str, jti: str) -> bool:
        """Port 1-1 từ authRepository.deleteOne({_id: payload.auth, jti: payload.jti})."""
        try:
            res = await self.collection.delete_one({"_id": ObjectId(auth_id), "jti": jti})
            return res.deleted_count > 0
        except Exception:
            return False

    # ─── Legacy methods kept for backward compatibility ──────────────
    async def get_session(self, jti: str) -> Optional[Dict[str, Any]]:
        """Lấy Auth session theo jti (legacy)."""
        return await self.collection.find_one({"jti": jti})

    async def revoke_session(self, jti: str) -> bool:
        """Thu hồi Auth session (legacy — dùng delete thay vì soft-revoke cho đúng NestJS)."""
        res = await self.collection.delete_one({"jti": jti})
        return res.deleted_count > 0
