import enum
from typing import Any, Dict, List, Optional, Type, Generic, TypeVar
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.context import get_current_partition_code

class DPQueryScope(str, enum.Enum):
    """Scope lọc dữ liệu theo Phân vùng (NODE, SUBTREE, ROOT_PATH, GLOBAL)."""
    NODE = "NODE"
    SUBTREE = "SUBTREE"
    ROOT_PATH = "ROOT_PATH"
    GLOBAL = "GLOBAL"


T = TypeVar("T")


class BaseMongoRepository(Generic[T]):
    """
    Hỗ trợ tự động gắn Data Partition filter theo scope NODE/SUBTREE/ROOT_PATH/GLOBAL.
    """

    def __init__(self, db: AsyncIOMotorDatabase, collection_name: str, scope: DPQueryScope = DPQueryScope.NODE):
        self.db = db
        self.collection = db[collection_name]
        self.scope = scope

    async def get_data_partition_condition(self, custom_scope: Optional[DPQueryScope] = None) -> Dict[str, Any]:
        scope = custom_scope or self.scope
        if scope == DPQueryScope.GLOBAL:
            return {}

        current_code = get_current_partition_code()
        if not current_code:
            return {}

        if scope == DPQueryScope.NODE:
            return {"dataPartitionCode": current_code}
        elif scope == DPQueryScope.SUBTREE:
            from app.modules.data_partition.service import DataPartitionService
            dp_service = DataPartitionService(self.db)
            subtree_items = await dp_service.get_subtree(current_code)
            subtree_codes = [item["ma"] for item in subtree_items] if subtree_items else [current_code]
            return {"dataPartitionCode": {"$in": subtree_codes}}
        elif scope == DPQueryScope.ROOT_PATH:
            from app.modules.data_partition.service import DataPartitionService
            dp_service = DataPartitionService(self.db)
            path_items = await dp_service.get_root_path(current_code)
            path_codes = [item["ma"] for item in path_items] if path_items else [current_code]
            return {"dataPartitionCode": {"$in": path_codes}}
        return {}

    async def create(self, document: Dict[str, Any]) -> Dict[str, Any]:
        partition_filter = await self.get_data_partition_condition(DPQueryScope.NODE)
        document.update(partition_filter)
        res = await self.collection.insert_one(document)
        document["_id"] = str(res.inserted_id)
        return document

    async def get_by_id(self, item_id: str) -> Optional[Dict[str, Any]]:
        from bson import ObjectId
        query = await self.get_data_partition_condition()
        try:
            query["_id"] = ObjectId(item_id)
        except Exception:
            query["_id"] = item_id

        doc = await self.collection.find_one(query)
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc

    async def get_page(self, page: int = 1, limit: int = 20, search: Optional[str] = None) -> Dict[str, Any]:
        query = await self.get_data_partition_condition()
        if search:
            query["$text"] = {"$search": search}

        total = await self.collection.count_documents(query)
        cursor = self.collection.find(query).skip((page - 1) * limit).limit(limit)

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

    async def update_by_id(self, item_id: str, update_doc: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        from bson import ObjectId
        query = await self.get_data_partition_condition()
        try:
            query["_id"] = ObjectId(item_id)
        except Exception:
            query["_id"] = item_id

        update_doc.pop("_id", None)
        res = await self.collection.find_one_and_update(
            query,
            {"$set": update_doc},
            return_document=True
        )
        if res:
            res["_id"] = str(res["_id"])
        return res

    async def delete_by_id(self, item_id: str) -> bool:
        from bson import ObjectId
        query = await self.get_data_partition_condition()
        try:
            query["_id"] = ObjectId(item_id)
        except Exception:
            query["_id"] = item_id

        res = await self.collection.delete_one(query)
        return res.deleted_count > 0

    async def get_many(self, limit: int = 100, conditions: Optional[Dict[str, Any]] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        query = await self.get_data_partition_condition()
        if conditions:
            query.update(conditions)
        if search:
            query["$text"] = {"$search": search}

        cursor = self.collection.find(query).limit(limit)
        items = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            items.append(doc)
        return items

    async def get_one(self, conditions: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        query = await self.get_data_partition_condition()
        if conditions:
            query.update(conditions)

        doc = await self.collection.find_one(query)
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc

    async def upsert(self, document: Dict[str, Any]) -> Dict[str, Any]:
        from bson import ObjectId
        item_id = document.get("_id") or document.get("id")
        query = await self.get_data_partition_condition()
        if item_id:
            try:
                query["_id"] = ObjectId(item_id)
            except Exception:
                query["_id"] = item_id

        document.pop("_id", None)
        res = await self.collection.find_one_and_update(
            query,
            {"$set": document},
            upsert=True,
            return_document=True
        )
        if res:
            res["_id"] = str(res["_id"])
        return res

    async def update_by_ids(self, ids: List[str], update_doc: Dict[str, Any]) -> int:
        if not ids:
            return 0
        from bson import ObjectId
        query = await self.get_data_partition_condition()
        object_ids = [ObjectId(i) if ObjectId.is_valid(i) else i for i in ids]
        query["_id"] = {"$in": object_ids}

        update_doc.pop("_id", None)
        res = await self.collection.update_many(query, {"$set": update_doc})
        return res.modified_count

    async def delete_by_ids(self, ids: List[str]) -> int:
        if not ids:
            return 0
        from bson import ObjectId
        query = await self.get_data_partition_condition()
        object_ids = [ObjectId(i) if ObjectId.is_valid(i) else i for i in ids]
        query["_id"] = {"$in": object_ids}

        res = await self.collection.delete_many(query)
        return res.deleted_count
