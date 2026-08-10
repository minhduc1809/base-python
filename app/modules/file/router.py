"""
File Router — port 1-1 từ file.controller.ts + file-public.controller.ts + file-internal.controller.ts.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, Header, Request, UploadFile, status
from fastapi.responses import Response
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
    ext: str = ""
    mimetype: str = "application/octet-stream"
    scope: str = "public"


class CompleteMultipartDto(BaseModel):
    fileId: str
    parts: List[dict] = []


# ─── POST /file — FileController.create (file.controller.ts) ────
@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def create(
    file: UploadFile = File(...),
    scope: Optional[str] = Form("public"),
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    request: Request = None,
):
    """Port 1-1 từ FileController.create (file.controller.ts:L28-50)."""
    service = FileService(db)
    content = await file.read()
    user_fullname = current_user.full_name or f"{current_user.lastname or ''} {current_user.firstname or ''}".strip() or current_user.username
    result = await service.create(
        user_id=str(current_user.id),
        user_fullname=user_fullname,
        user_username=current_user.username,
        dto={"scope": scope},
        file_bytes=content,
        original_name=file.filename,
        content_type=file.content_type,
        file_size=len(content),
    )
    return result


# ─── POST /file/multipart/init — FileController.initiateMultipartUpload ──
@router.post("/multipart/init")
async def init_upload_multipart(
    dto: InitMultipartDto,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Port 1-1 từ initiateMultipartUpload (file.service.ts:L533-605)."""
    service = FileService(db)
    user_fullname = current_user.full_name or f"{current_user.lastname or ''} {current_user.firstname or ''}".strip()
    return await service.initiate_multipart_upload(
        user_id=str(current_user.id),
        user_fullname=user_fullname,
        filename=dto.filename,
        size=dto.size,
        ext=dto.ext,
        mimetype=dto.mimetype,
        scope=dto.scope,
    )


# ─── POST /file/multipart/complete — FileController.completeMultipartUpload ──
@router.post("/multipart/complete")
async def complete_upload_multipart(
    dto: CompleteMultipartDto,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Port 1-1 từ clientCompleteMultipartUpload (file.service.ts:L607-629)."""
    service = FileService(db)
    return await service.client_complete_multipart_upload(dto.fileId, dto.parts)


# ─── GET /file/:id/info — FilePublicController.getFileInfo ──────
@router.get("/{id}/info")
async def get_file_info(
    id: str,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    authorization: Optional[str] = Header(None),
):
    """Port 1-1 từ getFileInfo (file.service.ts:L631-637)."""
    service = FileService(db)
    return await service.get_file_info(id, authorization)


# ─── GET /file/:id/:name — FilePublicController.getFileData ─────
@router.get("/{id}/{name}")
async def get_file_data(
    id: str,
    name: str,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    authorization: Optional[str] = Header(None),
):
    """Port 1-1 từ userGetFileData (file.service.ts:L333-342)."""
    service = FileService(db)
    file_bytes, mimetype = await service.get_file_data(id)
    return Response(content=file_bytes, media_type=mimetype)


# ─── DELETE /file/:id — FileController.deleteById ───────────────
@router.delete("/{file_id}", status_code=status.HTTP_200_OK)
async def delete_file_by_id(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Port 1-1 từ deleteById (file.service.ts:L431-441)."""
    service = FileService(db)
    return await service.delete_by_id(str(current_user.id), file_id)


# ─── Internal endpoints (file-internal.controller.ts) ───────────

@router.get("/{id}/data")
async def get_file_data_internal(
    id: str,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Port 1-1 từ FileInternalController.getFileData."""
    service = FileService(db)
    file_bytes, mimetype = await service.get_file_data(id)
    return Response(content=file_bytes, media_type=mimetype)


@router.put("/{id}/data")
async def update_file_data(
    id: str,
    file: UploadFile = File(...),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Port 1-1 từ FileInternalController.updateDataById."""
    service = FileService(db)
    content = await file.read()
    return await service.update_file_data(id, "internal", content, file.filename, file.content_type)


@router.post("/migrate/db/s3")
async def migrate_db_to_s3(db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
    """Port 1-1 từ FileInternalController.migrateDbToS3."""
    service = FileService(db)
    return await service.migrate_db_to_s3()


@router.post("/compress/files")
async def compress_files(db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
    """Port 1-1 từ FileInternalController.compressFiles."""
    service = FileService(db)
    return await service.compress_files()


@router.put("/{id}/upsert")
async def upsert_file_metadata(
    id: str,
    payload: dict,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Port 1-1 từ FileInternalController.upsertById."""
    service = FileService(db)
    return await service.upsert_by_id(id, payload)


@router.get("/presigned-url")
async def get_presigned_url(object_name: str, db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
    service = FileService(db)
    url = await service.get_presigned_url(object_name)
    return {"url": url}
