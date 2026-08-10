from fastapi import APIRouter
from app.common.base_framework.base_controller_factory import create_base_router, DPQueryScope

router = APIRouter(prefix="/ke-hoach-hoat-dong-nam", tags=["ke-hoach-hoat-dong"])


@router.get("/summary")
async def get_summary():
    return {"message": "Module Kế hoạch hoạt động năm (Python API)"}


base_router = create_base_router(
    collection_name="ke_hoach_hoat_dong",
    prefix="/ke-hoach-hoat-dong-nam",
    tags=["ke-hoach-hoat-dong"],
    scope=DPQueryScope.NODE,
)
router.include_router(base_router)
