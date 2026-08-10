"""
Data Partition Router — port 1-1 từ controllers/data-partition*.ts.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.common.base_framework.base_controller_factory import create_base_router, DPQueryScope
from app.core.context import get_current_partition_code
from app.core.database import get_mongo_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.data_partition.service import DataPartitionService, DataPartitionUserService

router = APIRouter(prefix="/data-partition", tags=["data-partition"])


class CreateDataPartitionRequest(BaseModel):
    ma: str
    ten: str
    parent_code: Optional[str] = None


class SyncDpUserBulkDto(BaseModel):
    bulk: List[dict] = []
    fullSync: bool = False
    syncGroup: Optional[str] = None


@router.get("/current")
async def get_current_partition():
    code = get_current_partition_code()
    return {"data_partition_code": code or "default"}


@router.get("/list")
async def list_partitions(db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
    service = DataPartitionService(db)
    return await service.model.list_all()


@router.get("/user/many/me")
async def get_many_me(
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Lấy danh sách data partition của chính người dùng hiện tại (khớp DataPartitionUserCommonController.getManyMe)."""
    coll = db["data_partition_users"]
    cursor = coll.find({"userId": str(current_user.id)})
    items = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        items.append(doc)
    return items


@router.post("/user/sync/bulk")
async def sync_dp_user_bulk(
    dto: SyncDpUserBulkDto,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Port 1-1 từ DataPartitionUserInternalController.syncBulk."""
    service = DataPartitionUserService(db)
    return await service.sync_bulk(dto.bulk, dto.fullSync, dto.syncGroup)


@router.get("/user/many/mode")
async def get_dp_user_by_mode(
    data_partition_code: str = Query(...),
    sso_id: str = Query(...),
    mode: str = Query("SUBTREE"),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Port 1-1 từ DataPartitionUserInternalController.getDpUserByMode."""
    service = DataPartitionUserService(db)
    return await service.get_dp_user_by_mode(data_partition_code, sso_id, mode)


@router.get("/{code}/root-path")
async def get_root_path(code: str, db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
    service = DataPartitionService(db)
    return await service.get_root_path(code)


@router.get("/{code}/subtree")
async def get_subtree(code: str, db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
    service = DataPartitionService(db)
    return await service.get_subtree(code)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_partition(
    dto: CreateDataPartitionRequest, db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    service = DataPartitionService(db)
    return await service.model.create_partition(ma=dto.ma, ten=dto.ten, parent_code=dto.parent_code)


# Base Class Router Integration
base_router = create_base_router(
    collection_name="data_partitions",
    prefix="/data-partition",
    tags=["data-partition"],
    scope=DPQueryScope.GLOBAL,
)
router.include_router(base_router)
