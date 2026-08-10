from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_mongo_db


class OneSignalUserModel:
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self.db = db or get_mongo_db()
        self.collection = self.db["one_signal_users"]

    async def update_user_device(
        self, player_id: str, user_id: str, auth_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Cập nhật/Đăng ký Player ID của thiết bị người dùng."""
        inactive_at = datetime.now(timezone.utc) + timedelta(days=30)
        res = await self.collection.find_one_and_update(
            {"playerId": player_id},
            {
                "$set": {
                    "playerId": player_id,
                    "user": str(user_id),
                    "auth": auth_id,
                    "inactiveAt": inactive_at,
                    "updatedAt": datetime.now(timezone.utc),
                }
            },
            upsert=True,
            return_document=True,
        )
        res["_id"] = str(res["_id"])
        return res
