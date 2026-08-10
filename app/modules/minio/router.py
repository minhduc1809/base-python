from fastapi import APIRouter
from app.modules.file.service import FileService

router = APIRouter(prefix="/minio", tags=["minio"])


@router.get("/buckets")
async def list_buckets():
    service = FileService()
    await service.ensure_bucket()
    return {"bucket": service.bucket, "status": "active"}
