"""
User Service — Port 1-1 từ user.service.ts (base-backend).
"""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.core.logging import logger
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.setting.constants import SettingKey


class UserService:
    """Port 1-1 từ UserService (user.service.ts)."""

    def __init__(self, db: AsyncSession, mongo_db: Optional[AsyncIOMotorDatabase] = None):
        self.db = db
        self.mongo_db = mongo_db

    async def on_application_bootstrap(self):
        """Port 1-1 từ onApplicationBootstrap (user.service.ts:L54-78).
        Tự động khởi tạo tài khoản admin mặc định khi ứng dụng khởi chạy nếu chưa tạo.
        """
        if not self.mongo_db:
            return

        settings_coll = self.mongo_db["settings"]
        init_data_doc = await settings_coll.find_one({"key": SettingKey.INIT_DATA.value})
        val = (init_data_doc or {}).get("value", {})

        if not val.get("isAdminCreated"):
            val["isAdminCreated"] = True
            admin_username = getattr(settings, "DEFAULT_ADMIN_USERNAME", "admin")
            admin_password = getattr(settings, "DEFAULT_ADMIN_PASSWORD", "admin123@A")

            # Check if admin user already exists in SQL DB
            stmt = select(User).where(User.username == admin_username)
            res = await self.db.execute(stmt)
            existing_user = res.scalar_one_or_none()

            if not existing_user:
                admin_user = User(
                    username=admin_username,
                    email="admin@administrator.com",
                    hashed_password=hash_password(admin_password),
                    system_role="ADMIN",
                    full_name="Administrator",
                )
                self.db.add(admin_user)
                await self.db.flush()
                logger.info("Admin user created on application bootstrap")

            await settings_coll.update_one(
                {"key": SettingKey.INIT_DATA.value},
                {"$set": {"key": SettingKey.INIT_DATA.value, "value": val}},
                upsert=True,
            )

    async def internal_get_by_id(self, user_id: int) -> Optional[User]:
        """Port 1-1 từ internalGetById(id)."""
        stmt = select(User).where(User.id == user_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()
