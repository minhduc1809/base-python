from fastapi import APIRouter
from app.common.base_framework.base_controller_factory import create_base_router, DPQueryScope

router = APIRouter(prefix="/data-process", tags=["data-process"])


@router.post("/execute")
async def execute_data_pipeline():
    return {"status": "success", "message": "Pipeline data process executed successfully"}


base_router = create_base_router(
    collection_name="data_process",
    prefix="/data-process",
    tags=["data-process"],
    scope=DPQueryScope.GLOBAL,
)
router.include_router(base_router)
