from typing import Optional
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_mongo_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.topic.models import UserTopicModel

router = APIRouter(prefix="/topic", tags=["topic"])


class TopicSubscribeDto(BaseModel):
    topic_name: str


@router.post("/subscribe", status_code=status.HTTP_200_OK)
async def subscribe_topic(
    dto: TopicSubscribeDto,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    model = UserTopicModel(db)
    res = await model.subscribe(user_id=str(current_user.id), topic_name=dto.topic_name)
    return {"message": f"Đã đăng ký topic {dto.topic_name} thành công", "data": res}


@router.post("/unsubscribe", status_code=status.HTTP_200_OK)
async def unsubscribe_topic(
    dto: TopicSubscribeDto,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    model = UserTopicModel(db)
    success = await model.unsubscribe(user_id=str(current_user.id), topic_name=dto.topic_name)
    return {"message": f"Đã hủy đăng ký topic {dto.topic_name}", "success": success}


from app.common.base_framework.base_controller_factory import create_base_router, DPQueryScope

base_router = create_base_router(
    collection_name="user_topics",
    prefix="/topic",
    tags=["topic"],
    scope=DPQueryScope.GLOBAL,
)
router.include_router(base_router)
