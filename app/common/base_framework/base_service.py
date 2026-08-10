from typing import Any, Dict, List, Optional
from app.common.base_framework.base_repository import BaseMongoRepository, DPQueryScope
from app.common.exceptions import AppException


class BaseService:
    """
    Port 1-1 từ BaseService trong NestJS (base.service.ts:L48-490).
    Xử lý transaction, notFoundCode, và ủy quyền cho Repository.
    """

    def __init__(self, repository: BaseMongoRepository):
        self.repository = repository

    async def create(self, dto: Dict[str, Any]) -> Dict[str, Any]:
        """Dịch 1-1 từ BaseService.create (base.service.ts:L121)."""
        return await self.repository.create(dto)

    async def get_by_id(self, item_id: str) -> Dict[str, Any]:
        """Dịch 1-1 từ BaseService.getById (base.service.ts:L178)."""
        res = await self.repository.get_by_id(item_id)
        if not res:
            raise AppException(status_code=404, message="Không tìm thấy bản ghi", error="Not Found")
        return res

    async def get_page(self, page: int = 1, limit: int = 20, search: Optional[str] = None) -> Dict[str, Any]:
        """Dịch 1-1 từ BaseService.getPage (base.service.ts:L210)."""
        return await self.repository.get_page(page=page, limit=limit, search=search)

    async def update_by_id(self, item_id: str, update_dto: Dict[str, Any]) -> Dict[str, Any]:
        """Dịch 1-1 từ BaseService.updateById (base.service.ts:L218)."""
        res = await self.repository.update_by_id(item_id, update_dto)
        if not res:
            raise AppException(status_code=404, message="Không tìm thấy bản ghi để cập nhật", error="Not Found")
        return res

    async def delete_by_id(self, item_id: str) -> Dict[str, Any]:
        """Dịch 1-1 từ BaseService.deleteById (base.service.ts:L382)."""
        success = await self.repository.delete_by_id(item_id)
        if not success:
            raise AppException(status_code=404, message="Không tìm thấy bản ghi để xóa", error="Not Found")
        return {"success": True, "id": item_id}
