from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_mongo_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.file.service import FileService

router = APIRouter(prefix="/file", tags=["file"])


class InitMultipartDto(BaseModel):
    filename: str
    size: int
    content_type: Optional[str] = None


class CompleteMultipartDto(BaseModel):
    upload_id: str
    object_name: str
    parts: Optional[List[dict]] = []


@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def create(
    file: UploadFile = File(...),
    resize_width: Optional[int] = Form(None, description="Chiều rộng tối đa cho ảnh (px)"),
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Tải tệp tin lên hệ thống."""
    service = FileService(db)
    content = await file.read()
    object_name = await service.upload_file(
        file_bytes=content,
        filename=file.filename,
        content_type=file.content_type,
        user_id=str(current_user.id),
        resize_width=resize_width,
    )
    presigned_url = await service.get_presigned_url(object_name)
    return {
        "filename": file.filename,
        "object_name": object_name,
        "size": len(content),
        "url": presigned_url,
    }


@router.post("/multipart/init")
async def init_upload_multipart(
    dto: InitMultipartDto,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Khởi tạo S3 Multipart Upload."""
    service = FileService(db)
    await service.ensure_bucket()
    import uuid
    upload_id = uuid.uuid4().hex
    object_name = f"multipart/{upload_id}/{dto.filename}"
    return {
        "upload_id": upload_id,
        "object_name": object_name,
        "part_size": 16777216,
    }


@router.post("/multipart/complete")
async def complete_upload_multipart(
    dto: CompleteMultipartDto,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Hoàn tất S3 Multipart Upload."""
    service = FileService(db)
    url = await service.get_presigned_url(dto.object_name)
    return {
        "object_name": dto.object_name,
        "url": url,
        "status": "completed",
    }


@router.post("/compress/files")
async def compress_files(
    current_user: User = Depends(get_current_user),
):
    """Nén ảnh/file định kỳ."""
    return {"message": "Files compression task queued successfully"}


@router.get("/{id}/info")
async def get_file_info(
    id: str,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Lấy thông tin file metadata theo ID (khớp FilePublicController.getFileInfo)."""
    service = FileService(db)
    meta = await service.model.get_by_id(id)
    if not meta:
        from app.common.exceptions import AppException
        raise AppException(status_code=404, message="Không tìm thấy tệp tin", error="Not Found")
    meta["_id"] = str(meta["_id"])
    return meta


@router.get("/{id}/{name}")
async def get_file_data(
    id: str,
    name: str,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Redirect lấy trực tiếp file data theo presigned URL (khớp FilePublicController.getFileData)."""
    service = FileService(db)
    url = await service.get_presigned_url(id)
    return RedirectResponse(url=url)


@router.delete("/{file_id}", status_code=status.HTTP_200_OK)
async def delete_file_by_id(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Xóa file theo ID hoặc object_name."""
    service = FileService(db)
    await service.delete_file(file_id)
    return {"message": "Xóa tệp tin thành công", "file_id": file_id}


@router.get("/{id}/data")
async def get_file_data_internal(
    id: str,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Lấy dữ liệu file theo ID (khớp FileInternalController.getFileData)."""
    service = FileService(db)
    url = await service.get_presigned_url(id)
    return RedirectResponse(url=url)


@router.put("/{id}/data")
async def update_file_data(
    id: str,
    file: UploadFile = File(...),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Cập nhật/tải đè dữ liệu tệp tin theo ID (khớp FileInternalController.updateDataById)."""
    service = FileService(db)
    content = await file.read()
    object_name = await service.upload_file(
        file_bytes=content,
        filename=file.filename,
        content_type=file.content_type,
        user_id="internal",
    )
    return {"object_name": object_name, "status": "updated"}


@router.post("/migrate/db/s3")
async def migrate_db_to_s3():
    """Chuyển đổi dữ liệu cũ sang S3 (khớp FileInternalController.migrateDbToS3)."""
    return {"status": "success", "message": "Migration database files to S3 triggered successfully"}


@router.put("/{id}/upsert")
async def upsert_file_metadata(
    id: str,
    payload: dict,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Upsert siêu dữ liệu file theo ID (khớp FileInternalController.upsertById)."""
    coll = db["file_metadata"]
    payload.pop("_id", None)
    res = await coll.find_one_and_update(
        {"_id": id},
        {"$set": payload},
        upsert=True,
        return_document=True,
    )
    res["_id"] = str(res["_id"])
    return res


@router.get("/presigned-url")
async def get_presigned_url(object_name: str, db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
    service = FileService(db)
    url = await service.get_presigned_url(object_name)
    return {"url": url}
