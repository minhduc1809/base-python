from typing import List, Optional
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_mongo_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.notification.service import NotificationService
from app.modules.one_signal.models import OneSignalUserModel

router = APIRouter(prefix="/one-signal", tags=["one-signal"])


class UpdateOneSignalUserDto(BaseModel):
    player_id: str


class OneSignalPushDto(BaseModel):
    title: str
    message: str
    player_ids: List[str]


@router.put("/user", status_code=status.HTTP_200_OK)
async def update_onesignal_user(
    dto: UpdateOneSignalUserDto,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Cập nhật Player ID của thiết bị người dùng."""
    model = OneSignalUserModel(db)
    res = await model.update_user_device(player_id=dto.player_id, user_id=str(current_user.id))
    return res


@router.post("/send", status_code=status.HTTP_200_OK)
async def send_onesignal(dto: OneSignalPushDto):
    service = NotificationService()
    success = await service.send_onesignal_push(
        title=dto.title, contents=dto.message, player_ids=dto.player_ids
    )
    return {"success": success}
