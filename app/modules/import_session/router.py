from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_mongo_db
from app.modules.import_session.service import ImportSessionService

router = APIRouter(prefix="/import-sessions", tags=["import-sessions"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_import_session(
    module_name: str,
    total_records: int = 0,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    service = ImportSessionService(db)
    return await service.create_import_session(module_name=module_name, total_records=total_records)


@router.get("/{session_id}")
async def get_import_session(
    session_id: str,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    service = ImportSessionService(db)
    session = await service.get_import_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/{session_id}/export-errors")
async def export_error_excel(
    session_id: str,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    service = ImportSessionService(db)
    try:
        content = await service.export_error_excel(session_id)
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=import_errors_{session_id}.xlsx"},
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
