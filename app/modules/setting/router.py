from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Path, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db_session
from app.modules.auth.dependencies import require_roles
from app.modules.auth.models import User
from app.modules.setting.constants import SettingKey
from app.modules.setting.schemas import SettingCreateOrUpdate, SettingResponse
from app.modules.setting.service import SettingService

router = APIRouter(prefix="/setting", tags=["setting"])


class SetSettingValueRequest(BaseModel):
    key: SettingKey
    value: Any
    description: Optional[str] = None


@router.get("", response_model=List[SettingResponse])
async def list_settings(
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_roles(["ADMIN", "SUPERADMIN"])),
):
    service = SettingService(db)
    return await service.get_all()


@router.get("/{key}/value")
async def get_setting_value(
    key: SettingKey = Path(..., description="Tên khóa cài đặt"),
    db: AsyncSession = Depends(get_db_session),
):
    service = SettingService(db)
    val = await service.get_setting_value(key)
    return {"key": key.value, "value": val}


@router.put("/value")
async def set_setting_value(
    dto: SetSettingValueRequest,
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_roles(["ADMIN", "SUPERADMIN"])),
):
    service = SettingService(db)
    setting = await service.set_setting_value(dto.key, dto.value, description=dto.description)
    return {"key": setting.key, "value": setting.value}
