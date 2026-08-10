from typing import Any, Dict, List, Optional, Type
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_mongo_db


class BaseCrudQuery(BaseModel):
    page: int = 1
    limit: int = 20
    search: Optional[str] = None


def add_mongo_crud_routes(
    router: APIRouter,
    collection_name: str,
    create_schema: Optional[Type[BaseModel]] = None,
    update_schema: Optional[Type[BaseModel]] = None,
):
    """
    Tự động sinh đầy đủ các API CRUD chuẩn (BaseControllerFactory) cho MongoDB collection.
    Bao gồm: getPage, getOne, getMany, getById, create, updateById, updateByIds, deleteById, deleteByIds, definition, export, import.
    """

    @router.get("", summary="Get Page (Phân trang & Tìm kiếm)")
    @router.get("/page", summary="Get Page")
    async def get_page(
        page: int = Query(1, ge=1),
        limit: int = Query(20, ge=1, le=100),
        search: Optional[str] = Query(None),
        db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    ):
        coll = db[collection_name]
        query = {}
        if search:
            query["$text"] = {"$search": search}

        total = await coll.count_documents(query)
        cursor = coll.find(query).skip((page - 1) * limit).limit(limit)

        items = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            items.append(doc)

        return {
            "items": items,
            "data": items,
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": (total + limit - 1) // limit if limit > 0 else 1,
        }

    @router.get("/one", summary="Get One Record")
    async def get_one(
        id: Optional[str] = Query(None),
        code: Optional[str] = Query(None),
        db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    ):
        from bson import ObjectId
        coll = db[collection_name]
        query = {}
        if id:
            try:
                query["_id"] = ObjectId(id)
            except Exception:
                query["_id"] = id
        elif code:
            query["ma"] = code

        doc = await coll.find_one(query)
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc

    @router.get("/many", summary="Get Many Records")
    async def get_many(
        limit: int = Query(100, ge=1, le=500),
        db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    ):
        coll = db[collection_name]
        cursor = coll.find({}).limit(limit)
        items = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            items.append(doc)
        return items

    @router.get("/definition", summary="Entity Definition Metadata")
    async def get_definition():
        return {
            "collection": collection_name,
            "fields": ["_id", "ma", "ten", "status", "createdAt", "updatedAt"],
        }

    @router.get("/{item_id}", summary="Get By ID")
    async def get_by_id(
        item_id: str,
        db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    ):
        from bson import ObjectId
        from app.common.exceptions import AppException

        coll = db[collection_name]
        try:
            doc = await coll.find_one({"_id": ObjectId(item_id)})
        except Exception:
            doc = await coll.find_one({"_id": item_id})

        if not doc:
            raise AppException(status_code=404, message=f"Không tìm thấy bản ghi '{item_id}'", error="Not Found")
        doc["_id"] = str(doc["_id"])
        return doc

    @router.post("", status_code=status.HTTP_201_CREATED, summary="Create Record")
    async def create_record(
        payload: Dict[str, Any],
        db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    ):
        from datetime import datetime, timezone
        coll = db[collection_name]
        payload["createdAt"] = datetime.now(timezone.utc)
        res = await coll.insert_one(payload)
        payload["_id"] = str(res.inserted_id)
        return payload

    @router.put("", summary="Update Many Records")
    async def update_many_records(
        payload: Dict[str, Any],
        db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    ):
        coll = db[collection_name]
        ids = payload.get("ids", [])
        data = payload.get("data", {})
        if ids:
            from bson import ObjectId
            object_ids = [ObjectId(i) if ObjectId.is_valid(i) else i for i in ids]
            res = await coll.update_many({"_id": {"$in": object_ids}}, {"$set": data})
            return {"updated": res.modified_count}
        return {"updated": 0}

    @router.put("/{item_id}", summary="Update By ID")
    async def update_record(
        item_id: str,
        payload: Dict[str, Any],
        db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    ):
        from bson import ObjectId
        from datetime import datetime, timezone
        from app.common.exceptions import AppException

        coll = db[collection_name]
        payload["updatedAt"] = datetime.now(timezone.utc)
        payload.pop("_id", None)

        try:
            res = await coll.find_one_and_update(
                {"_id": ObjectId(item_id)},
                {"$set": payload},
                return_document=True,
            )
        except Exception:
            res = await coll.find_one_and_update(
                {"_id": item_id},
                {"$set": payload},
                return_document=True,
            )

        if not res:
            raise AppException(status_code=404, message=f"Không tìm thấy bản ghi '{item_id}'", error="Not Found")
        res["_id"] = str(res["_id"])
        return res

    @router.delete("", status_code=status.HTTP_200_OK, summary="Delete Many Records")
    async def delete_many_records(
        ids: List[str] = Query([]),
        db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    ):
        coll = db[collection_name]
        if ids:
            from bson import ObjectId
            object_ids = [ObjectId(i) if ObjectId.is_valid(i) else i for i in ids]
            res = await coll.delete_many({"_id": {"$in": object_ids}})
            return {"deleted": res.deleted_count}
        return {"deleted": 0}

    @router.delete("/{item_id}", status_code=status.HTTP_200_OK, summary="Delete By ID")
    async def delete_record(
        item_id: str,
        db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    ):
        from bson import ObjectId
        from app.common.exceptions import AppException

        coll = db[collection_name]
        try:
            res = await coll.delete_one({"_id": ObjectId(item_id)})
        except Exception:
            res = await coll.delete_one({"_id": item_id})

        if res.deleted_count == 0:
            raise AppException(status_code=404, message=f"Không tìm thấy bản ghi '{item_id}'", error="Not Found")
        return {"message": "Xóa bản ghi thành công", "id": item_id}

    @router.post("/import", summary="Import Data Batch")
    async def import_records(
        items: List[Dict[str, Any]],
        db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    ):
        coll = db[collection_name]
        if items:
            res = await coll.insert_many(items)
            return {"inserted": len(res.inserted_ids)}
        return {"inserted": 0}

    @router.post("/export", summary="Export Data Batch")
    async def export_records(
        query: Dict[str, Any] = {},
        db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    ):
        coll = db[collection_name]
        cursor = coll.find(query).limit(1000)
        items = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            items.append(doc)
        return {"items": items, "total": len(items)}
