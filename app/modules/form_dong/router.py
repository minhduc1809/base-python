from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.common.base_framework.base_controller_factory import create_base_router, DPQueryScope
from app.core.database import get_mongo_db
from app.modules.form_dong.schemas import FormDongCreate, FormDongResponseSubmission
from app.modules.form_dong.service import FormDongService

router = APIRouter(prefix="/form-dong", tags=["form-dong"])


@router.post("/schema", status_code=status.HTTP_201_CREATED)
async def create_form_schema(
    dto: FormDongCreate, db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    service = FormDongService(db)
    return await service.create_schema(dto)


@router.get("/schema/{ma_form}")
async def get_form_schema(
    ma_form: str, db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    service = FormDongService(db)
    return await service.get_schema_by_code(ma_form)


@router.post("/submit", status_code=status.HTTP_201_CREATED)
async def submit_form_data(
    submission: FormDongResponseSubmission,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    service = FormDongService(db)
    return await service.submit_response(submission)


@router.get("/submissions/{ma_form}")
async def list_form_submissions(
    ma_form: str,
    limit: int = Query(50, ge=1, le=500),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    service = FormDongService(db)
    return await service.list_submissions(ma_form, limit=limit)


base_router = create_base_router(
    collection_name="form_dong",
    prefix="/form-dong",
    tags=["form-dong"],
    scope=DPQueryScope.NODE,
)
router.include_router(base_router)
