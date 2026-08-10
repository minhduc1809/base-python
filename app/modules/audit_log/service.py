from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.context import get_current_partition_code, get_current_user_id


class AuditLogService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["audit_logs"]

    async def log_action(
        self,
        action: str,
        module: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
        u_code: Optional[str] = None,
        u_name: Optional[str] = None,
        u_email: Optional[str] = None,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_type: str = "http",
    ) -> Dict[str, Any]:
        partition_code = get_current_partition_code()
        current_user = user_id or get_current_user_id()

        doc = {
            "uId": current_user,
            "uCode": u_code,
            "uName": u_name,
            "uEmail": u_email,
            "action": action,
            "module": module,
            "requestType": request_type,
            "ip": ip,
            "userAgent": user_agent,
            "details": details,
            "data_partition_code": partition_code,
            "timestamp": datetime.now(timezone.utc),
        }
        res = await self.collection.insert_one(doc)
        doc["_id"] = str(res.inserted_id)
        return doc

    async def get_logs_for_user(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"uId": str(user_id)}).sort("timestamp", -1).limit(limit)
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results

    async def get_logs(
        self, module: Optional[str] = None, limit: int = 50, skip: int = 0
    ) -> List[Dict[str, Any]]:
        partition_code = get_current_partition_code()
        query = {}
        if partition_code:
            query["data_partition_code"] = partition_code
        if module:
            query["module"] = module

        cursor = self.collection.find(query).sort("timestamp", -1).skip(skip).limit(limit)
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results

    async def clear_old_logs(self, years: int = 4) -> int:
        """Xóa log cũ hơn N năm (mặc định 4 năm)."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=years * 365)
        res = await self.collection.delete_many({"createdAt": {"$lte": cutoff}})
        return res.deleted_count
