from typing import List, Optional, Set
from fastapi import APIRouter, Depends, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_mongo_db
from app.common.base_framework.base_repository import BaseMongoRepository, DPQueryScope
from app.common.base_framework.base_service import BaseService


def create_base_router(
    collection_name: str,
    prefix: Optional[str] = None,
    tags: Optional[List[str]] = None,
    scope: DPQueryScope = DPQueryScope.NODE,
    disabled_methods: Optional[Set[str]] = None,
) -> APIRouter:
    """
    Port 1-1 từ BaseControllerFactory trong NestJS (base-controller-factory.ts:L63-416).
    Tự động sinh các route CRUD chuẩn kế thừa từ BaseService và BaseMongoRepository.
    Cho phép vô hiệu hóa (disable) các route nhạy cảm (vd: audit-log tắt create/update/delete).
    """
    router_prefix = prefix or f"/{collection_name.replace('_', '-')}"
    router_tags = tags or [collection_name]
    router = APIRouter(prefix=router_prefix, tags=router_tags)
    disabled = disabled_methods or set()

    def get_service(db: AsyncIOMotorDatabase = Depends(get_mongo_db)) -> BaseService:
        repo = BaseMongoRepository(db, collection_name=collection_name, scope=scope)
        return BaseService(repo)

    if "getPage" not in disabled:
        @router.get("", summary="Get Page")
        @router.get("/page", summary="Get Page")
        async def get_page(
            page: int = Query(1, ge=1),
            limit: int = Query(20, ge=1, le=100),
            search: Optional[str] = Query(None),
            service: BaseService = Depends(get_service),
        ):
            return await service.get_page(page=page, limit=limit, search=search)

    if "getById" not in disabled:
        @router.get("/{item_id}", summary="Get By ID")
        async def get_by_id(
            item_id: str,
            service: BaseService = Depends(get_service),
        ):
            return await service.get_by_id(item_id)

    if "create" not in disabled:
        @router.post("", status_code=status.HTTP_201_CREATED, summary="Create Record")
        async def create(
            payload: dict,
            service: BaseService = Depends(get_service),
        ):
            return await service.create(payload)

    if "updateById" not in disabled:
        @router.put("/{item_id}", summary="Update By ID")
        async def update_by_id(
            item_id: str,
            payload: dict,
            service: BaseService = Depends(get_service),
        ):
            return await service.update_by_id(item_id, payload)

    if "deleteById" not in disabled:
        @router.delete("/{item_id}", summary="Delete By ID")
        async def delete_by_id(
            item_id: str,
            service: BaseService = Depends(get_service),
        ):
            return await service.delete_by_id(item_id)

    # Import / Export Definitions matching NestJS BaseControllerFactory
    if "importDefinition" not in disabled:
        @router.get("/import/definition", summary="Import Definition")
        async def get_import_definition():
            return {"collection": collection_name, "supported_columns": ["ma", "ten", "status"]}

    if "exportDefinition" not in disabled:
        @router.get("/export/definition", summary="Export Definition")
        async def get_export_definition():
            return {"collection": collection_name, "exportable_columns": ["_id", "ma", "ten", "dataPartitionCode"]}

    return router
