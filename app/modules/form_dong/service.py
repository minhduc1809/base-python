from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.common.exceptions import AppException
from app.core.context import get_current_partition_code
from app.modules.form_dong.schemas import FormDongCreate, FormDongResponseSubmission


class FormDongService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.schemas_collection = db["form_dong_schemas"]
        self.submissions_collection = db["form_dong_submissions"]

    async def create_schema(self, dto: FormDongCreate) -> Dict[str, Any]:
        partition_code = get_current_partition_code()
        now = datetime.now(timezone.utc)
        doc = {
            "ma_form": dto.ma_form,
            "maForm": dto.ma_form,
            "ten_form": dto.ten_form,
            "tenForm": dto.ten_form,
            "fields": dto.fields,
            "config": dto.config or {},
            "data_partition_code": partition_code,
            "dataPartitionCode": partition_code,
            "created_at": now,
            "createdAt": now,
            "updated_at": now,
            "updatedAt": now,
        }
        result = await self.schemas_collection.insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        return doc

    async def get_schema_by_code(self, ma_form: str) -> Dict[str, Any]:
        partition_code = get_current_partition_code()
        query = {"$or": [{"ma_form": ma_form}, {"maForm": ma_form}]}
        if partition_code:
            query["$and"] = [{"$or": [{"data_partition_code": partition_code}, {"dataPartitionCode": partition_code}]}]

        doc = await self.schemas_collection.find_one({"$or": [{"ma_form": ma_form}, {"maForm": ma_form}]})
        if not doc:
            raise AppException(status_code=404, message=f"Form '{ma_form}' không tồn tại", error="Not Found")
        doc["_id"] = str(doc["_id"])
        return doc

    async def submit_response(self, submission: FormDongResponseSubmission) -> Dict[str, Any]:
        partition_code = get_current_partition_code()
        now = datetime.now(timezone.utc)
        # Verify schema exists
        await self.get_schema_by_code(submission.ma_form)

        doc = {
            "ma_form": submission.ma_form,
            "maForm": submission.ma_form,
            "data": submission.data,
            "metadata": submission.metadata or {},
            "data_partition_code": partition_code,
            "dataPartitionCode": partition_code,
            "created_at": now,
            "createdAt": now,
        }
        result = await self.submissions_collection.insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        return doc

    async def list_submissions(self, ma_form: str, limit: int = 50) -> List[Dict[str, Any]]:
        query = {"$or": [{"ma_form": ma_form}, {"maForm": ma_form}]}
        cursor = self.submissions_collection.find(query).limit(limit)
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results
