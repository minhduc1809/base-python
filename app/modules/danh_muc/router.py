from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db_session
from app.modules.danh_muc.schemas import DanhMucCreate, DanhMucResponse, DanhMucUpdate
from app.modules.danh_muc.service import DanhMucService

router = APIRouter(prefix="/danh-muc", tags=["danh-muc"])


@router.get("", response_model=List[DanhMucResponse])
@router.get("/page", response_model=List[DanhMucResponse])
@router.get("/many", response_model=List[DanhMucResponse])
async def list_danh_muc(
    loai: Optional[str] = Query(None, description="Lọc theo loại danh mục"),
    db: AsyncSession = Depends(get_db_session),
):
    service = DanhMucService(db)
    return await service.get_all(loai=loai)


@router.get("/one", response_model=Optional[DanhMucResponse])
async def get_one_danh_muc(id: Optional[int] = Query(None), db: AsyncSession = Depends(get_db_session)):
    if not id:
        return None
    service = DanhMucService(db)
    return await service.get_by_id(id)


@router.get("/{item_id}", response_model=DanhMucResponse)
async def get_danh_muc(item_id: int, db: AsyncSession = Depends(get_db_session)):
    service = DanhMucService(db)
    return await service.get_by_id(item_id)


@router.post("", response_model=DanhMucResponse, status_code=status.HTTP_201_CREATED)
async def create_danh_muc(
    dto: DanhMucCreate, db: AsyncSession = Depends(get_db_session)
):
    service = DanhMucService(db)
    return await service.create(dto)


@router.put("/{item_id}", response_model=DanhMucResponse)
async def update_danh_muc(
    item_id: int, dto: DanhMucUpdate, db: AsyncSession = Depends(get_db_session)
):
    service = DanhMucService(db)
    return await service.update(item_id, dto)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_danh_muc(item_id: int, db: AsyncSession = Depends(get_db_session)):
    service = DanhMucService(db)
    await service.delete(item_id)
