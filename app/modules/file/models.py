"""
File Model - Thao tác lưu trữ dữ liệu tập tin trong MongoDB.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_mongo_db


class FileModel:
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self.db = db or get_mongo_db()
        self.collection = self.db["files"]

    # ─── create (fileRepository.create(doc)) ─────────────────────────
    async def create_file(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Tạo file record trong MongoDB."""
        doc["createdAt"] = datetime.now(timezone.utc)
        res = await self.collection.insert_one(doc)
        doc["_id"] = str(res.inserted_id)
        return doc

    # ─── getById (fileRepository.getById(id)) ───────────────────────
    async def get_by_id(self, file_id: str, projection: Optional[dict] = None) -> Optional[Dict[str, Any]]:
        try:
            return await self.collection.find_one({"_id": ObjectId(file_id)}, projection)
        except Exception:
            return await self.collection.find_one({"objectName": file_id}, projection)

    # ─── updateById (fileRepository.updateById(id, data)) ───────────
    async def update_by_id(self, file_id: str, update: dict) -> bool:
        try:
            res = await self.collection.update_one(
                {"_id": ObjectId(file_id)},
                {"$set": update},
            )
            return res.modified_count > 0
        except Exception:
            return False

    # ─── deleteOne({_id, author}) — file.service.ts:L433-436 ───────
    async def delete_one_by_author(self, file_id: str, author_id: str) -> Optional[Dict[str, Any]]:
        """Port 1-1 từ fileRepository.deleteOne({_id: id, author: user._id})."""
        try:
            doc = await self.collection.find_one_and_delete({
                "_id": ObjectId(file_id),
                "author": author_id,
            })
            if doc:
                doc["_id"] = str(doc["_id"])
            return doc
        except Exception:
            return None

    # ─── getMany (fileRepository.getMany(conditions, query)) ────────
    async def get_many(self, conditions: dict, projection: Optional[dict] = None) -> List[Dict[str, Any]]:
        cursor = self.collection.find(conditions, projection)
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results

    # ─── upsertById (fileRepository.updateById(id, file, {upsert:true})) ──
    async def upsert_by_id(self, file_id: str, file_data: dict) -> Dict[str, Any]:
        file_data.pop("_id", None)
        try:
            res = await self.collection.find_one_and_update(
                {"_id": ObjectId(file_id)},
                {"$set": file_data},
                upsert=True,
                return_document=True,
            )
            res["_id"] = str(res["_id"])
            return res
        except Exception:
            res = await self.collection.find_one_and_update(
                {"_id": file_id},
                {"$set": file_data},
                upsert=True,
                return_document=True,
            )
            res["_id"] = str(res["_id"])
            return res

    # ─── exists (fileRepository.exists(conditions)) ─────────────────
    async def exists(self, conditions: dict) -> bool:
        return await self.collection.count_documents(conditions, limit=1) > 0

    # ─── Legacy methods ─────────────────────────────────────────────
    async def save_file_meta(
        self, filename: str, object_name: str, size: int, content_type: str, user_id: str
    ) -> Dict[str, Any]:
        doc = {
            "name": filename,
            "objectName": object_name,
            "size": size,
            "mimetype": content_type,
            "author": str(user_id),
            "storageType": "s3",
            "data": object_name,
            "createdAt": datetime.now(timezone.utc),
        }
        res = await self.collection.insert_one(doc)
        doc["_id"] = str(res.inserted_id)
        return doc

    async def delete_meta(self, file_id: str) -> bool:
        try:
            res = await self.collection.delete_one({"_id": ObjectId(file_id)})
            return res.deleted_count > 0
        except Exception:
            res = await self.collection.delete_one({"objectName": file_id})
            return res.deleted_count > 0
