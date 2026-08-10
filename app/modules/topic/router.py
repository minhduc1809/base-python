"""
Topic Router — port 1-1 từ topic.controller.ts (base-backend).
"""
from typing import Optional
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_mongo_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.topic.service import TopicService
from app.common.base_framework.base_controller_factory import create_base_router, DPQueryScope

router = APIRouter(prefix="/topic", tags=["topic"])


class TopicSubscribeDto(BaseModel):
    topic: str  # id hoặc name của topic


@router.post("/subscribe", status_code=status.HTTP_200_OK)
async def subscribe_topic(
    dto: TopicSubscribeDto,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Port 1-1 từ TopicController.userSubscribeTopic (topic.controller.ts)."""
    service = TopicService(db)
    res = await service.user_subscribe_topic(user_id=str(current_user.id), topic_id_or_name=dto.topic)
    return {"message": "Đã đăng ký topic thành công", "data": res}


@router.post("/unsubscribe", status_code=status.HTTP_200_OK)
async def unsubscribe_topic(
    dto: TopicSubscribeDto,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    res = await db["user_topics"].update_one(
        {"userId": str(current_user.id)},
        {"$pull": {"subscriptions": {"topic": dto.topic}}},
    )
    return {"message": f"Đã hủy đăng ký topic {dto.topic}", "success": res.modified_count > 0}


base_router = create_base_router(
    collection_name="user_topics",
    prefix="/topic",
    tags=["topic"],
    scope=DPQueryScope.GLOBAL,
)
router.include_router(base_router)
