from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_mongo_db
from app.modules.khao_sat.schemas import CauTraLoiKhaoSatSubmit, DotKhaoSatCreate
from app.modules.khao_sat.service import KhaoSatService

router = APIRouter(prefix="/khao-sat", tags=["khao-sat"])


@router.post("/dot-khao-sat", status_code=status.HTTP_201_CREATED)
async def create_dot_khao_sat(
    dto: DotKhaoSatCreate, db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    service = KhaoSatService(db)
    return await service.create_dot_khao_sat(dto)


@router.post("/submit", status_code=status.HTTP_201_CREATED)
async def submit_answers(
    dto: CauTraLoiKhaoSatSubmit, db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    service = KhaoSatService(db)
    return await service.submit_answers(dto)


from app.common.base_framework.base_controller_factory import create_base_router, DPQueryScope

base_router = create_base_router(
    collection_name="khao_sat",
    prefix="/khao-sat",
    tags=["khao-sat"],
    scope=DPQueryScope.NODE,
)
router.include_router(base_router)
