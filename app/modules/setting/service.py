from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.exceptions import AppException
from app.modules.setting.constants import SettingKey
from app.modules.setting.models import Setting


class SettingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> List[Setting]:
        stmt = select(Setting)
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def get_by_key(self, key: str) -> Optional[Setting]:
        stmt = select(Setting).where(Setting.key == key)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_setting_value(self, key: SettingKey) -> Optional[Any]:
        setting = await self.get_by_key(key.value if isinstance(key, SettingKey) else key)
        return setting.value if setting else None

    async def set_setting_value(self, key: SettingKey, value: Any, description: Optional[str] = None) -> Setting:
        key_str = key.value if isinstance(key, SettingKey) else key
        existing = await self.get_by_key(key_str)
        if existing:
            existing.value = value
            if description:
                existing.description = description
            item = existing
        else:
            item = Setting(key=key_str, value=value, description=description)
            self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)
        return item
