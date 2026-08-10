from fastapi import APIRouter

router = APIRouter(prefix="/common-provider", tags=["common-provider"])


@router.get("/status")
async def get_common_providers_status():
    return {"providers": ["database", "redis", "minio", "logging"], "status": "healthy"}
