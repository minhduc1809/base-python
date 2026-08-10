from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.exceptions import AppException
from app.core.context import get_current_partition_code
from app.modules.danh_muc.models import DanhMuc
from app.modules.danh_muc.schemas import DanhMucCreate, DanhMucUpdate


class DanhMucService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, loai: Optional[str] = None) -> List[DanhMuc]:
        partition_code = get_current_partition_code()
        stmt = select(DanhMuc)
        if partition_code:
            stmt = stmt.where(DanhMuc.data_partition_code == partition_code)
        if loai:
            stmt = stmt.where(DanhMuc.loai == loai)
        stmt = stmt.order_by(DanhMuc.thu_tu.asc(), DanhMuc.created_at.desc())

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, item_id: int) -> DanhMuc:
        partition_code = get_current_partition_code()
        stmt = select(DanhMuc).where(DanhMuc.id == item_id)
        if partition_code:
            stmt = stmt.where(DanhMuc.data_partition_code == partition_code)

        result = await self.db.execute(stmt)
        item = result.scalar_one_or_none()
        if not item:
            raise AppException(status_code=404, message="Danh mục không tồn tại", error="Not Found")
        return item

    async def create(self, dto: DanhMucCreate) -> DanhMuc:
        partition_code = get_current_partition_code()

        # Check existing code
        stmt = select(DanhMuc).where(DanhMuc.ma == dto.ma)
        if partition_code:
            stmt = stmt.where(DanhMuc.data_partition_code == partition_code)
        existing = await self.db.execute(stmt)
        if existing.scalar_one_or_none():
            raise AppException(status_code=400, message=f"Mã danh mục '{dto.ma}' đã tồn tại", error="Conflict")

        item = DanhMuc(
            ma=dto.ma,
            ten=dto.ten,
            loai=dto.loai,
            mo_ta=dto.mo_ta,
            thu_tu=dto.thu_tu,
            trang_thai=dto.trang_thai,
            data_partition_code=partition_code,
        )
        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def update(self, item_id: int, dto: DanhMucUpdate) -> DanhMuc:
        item = await self.get_by_id(item_id)
        update_data = dto.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(item, field, value)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def delete(self, item_id: int) -> bool:
        item = await self.get_by_id(item_id)
        await self.db.delete(item)
        return True
