from typing import List, Optional
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_mongo_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.notification.service import NotificationService

router = APIRouter(prefix="/notification", tags=["notification"])


class CreateNotificationDto(BaseModel):
    title: str
    content: str
    receiver_type: str = "USER"  # USER, TOPIC
    users: Optional[List[str]] = []
    topics: Optional[List[str]] = []
    player_ids: Optional[List[str]] = []


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_notification(
    dto: CreateNotificationDto,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Tạo notification và kích hoạt push thông báo."""
    service = NotificationService(db)
    return await service.create_notification(
        title=dto.title,
        content=dto.content,
        receiver_type=dto.receiver_type,
        sender_id=str(current_user.id),
        sender_name=current_user.full_name or current_user.username,
        users=dto.users,
        topics=dto.topics,
        player_ids=dto.player_ids,
    )


from app.common.base_framework.base_controller_factory import create_base_router, DPQueryScope

base_router = create_base_router(
    collection_name="notifications",
    prefix="/notification",
    tags=["notification"],
    scope=DPQueryScope.GLOBAL,
)
router.include_router(base_router)
