from fastapi import APIRouter
from app.common.base_framework.base_controller_factory import create_base_router, DPQueryScope

router = APIRouter(prefix="/diem-ren-luyen-v2", tags=["diem-ren-luyen"])


@router.get("/summary")
async def get_summary():
    return {"message": "Module Điểm rèn luyện V2 (Python API)"}


base_router = create_base_router(
    collection_name="diem_ren_luyen",
    prefix="/diem-ren-luyen-v2",
    tags=["diem-ren-luyen"],
    scope=DPQueryScope.NODE,
)
router.include_router(base_router)
