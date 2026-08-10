from typing import Any, Dict, List, Optional
from app.common.base_framework.base_repository import BaseMongoRepository, DPQueryScope
from app.common.exceptions import AppException


class BaseService:
    """
    Xử lý transaction, notFoundCode, và ủy quyền cho Repository.
    """

    def __init__(self, repository: BaseMongoRepository):
        self.repository = repository

    async def create(self, dto: Dict[str, Any]) -> Dict[str, Any]:
        return await self.repository.create(dto)

    async def get_by_id(self, item_id: str) -> Dict[str, Any]:
        res = await self.repository.get_by_id(item_id)
        if not res:
            raise AppException(status_code=404, message="Không tìm thấy bản ghi", error="Not Found")
        return res

    async def get_page(self, page: int = 1, limit: int = 20, search: Optional[str] = None) -> Dict[str, Any]:
        return await self.repository.get_page(page=page, limit=limit, search=search)

    async def update_by_id(self, item_id: str, update_dto: Dict[str, Any]) -> Dict[str, Any]:
        res = await self.repository.update_by_id(item_id, update_dto)
        if not res:
            raise AppException(status_code=404, message="Không tìm thấy bản ghi để cập nhật", error="Not Found")
        return res

    async def delete_by_id(self, item_id: str) -> Dict[str, Any]:
        success = await self.repository.delete_by_id(item_id)
        if not success:
            raise AppException(status_code=404, message="Không tìm thấy bản ghi để xóa", error="Not Found")
        return {"success": True, "id": item_id}

    async def get_many(self, limit: int = 100, conditions: Optional[Dict[str, Any]] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        return await self.repository.get_many(limit=limit, conditions=conditions, search=search)

    async def get_one(self, conditions: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        return await self.repository.get_one(conditions=conditions)

    async def upsert(self, dto: Dict[str, Any]) -> Dict[str, Any]:
        return await self.repository.upsert(dto)

    async def update_by_ids(self, ids: List[str], update_dto: Dict[str, Any]) -> Dict[str, Any]:
        count = await self.repository.update_by_ids(ids, update_dto)
        return {"updated": count}

    async def delete_by_ids(self, ids: List[str]) -> Dict[str, Any]:
        count = await self.repository.delete_by_ids(ids)
        return {"deleted": count}
