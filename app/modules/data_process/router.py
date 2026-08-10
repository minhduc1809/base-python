from typing import Any, Dict, List
from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_mongo_db
from app.modules.data_process.service import DataProcessService

router = APIRouter(prefix="/data-process", tags=["data-process"])


@router.post("/batch", status_code=status.HTTP_201_CREATED)
async def process_data_batch(
    name: str,
    items: List[Dict[str, Any]],
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    service = DataProcessService(db)
    return await service.process_data_batch(name, items)


@router.get("/aggregate")
async def aggregate_data_process_status(
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    service = DataProcessService(db)
    return await service.aggregate_data_process_status()
