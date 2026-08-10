"""
Data Partition Service — Port 1-1 từ data-partition.service.ts và data-partition-user.service.ts.
"""
from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.common.exceptions import AppException
from app.modules.data_partition.models import DataPartitionModel


class DataPartitionService:
    """Port 1-1 từ DataPartitionService (data-partition.service.ts)."""

    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self.model = DataPartitionModel(db)
        self.db = db

    async def get_root_path(self, data_partition_code: str) -> List[Dict[str, Any]]:
        """Truy vết danh sách các nút cha từ node hiện tại ngược lên gốc (Root Path)."""
        curr = await self.model.get_by_code(data_partition_code)
        path: List[Dict[str, Any]] = []
        visited = set()

        while curr and curr.get("ma") not in visited:
            visited.add(curr["ma"])
            curr_copy = dict(curr)
            curr_copy["_id"] = str(curr_copy["_id"])
            path.append(curr_copy)

            parent_code = curr.get("parentCode")
            if parent_code:
                curr = await self.model.get_by_code(parent_code)
            else:
                break

        return path

    async def get_subtree(self, data_partition_code: str) -> List[Dict[str, Any]]:
        """Truy vấn danh sách toàn bộ các nút con thuộc cây phân cấp (Subtree)."""
        curr = await self.model.get_by_code(data_partition_code)
        if not curr:
            return []

        subtree: List[Dict[str, Any]] = []
        curr_copy = dict(curr)
        curr_copy["_id"] = str(curr_copy["_id"])

        children = [curr_copy]
        while children:
            subtree.extend(children)
            parent_codes = [c["ma"] for c in children]
            raw_children = await self.model.list_all({"parentCode": {"$in": parent_codes}})
            visited_codes = {s["ma"] for s in subtree}
            children = [c for c in raw_children if c["ma"] not in visited_codes]

        return subtree


class DataPartitionUserService:
    """Port 1-1 từ DataPartitionUserService (data-partition-user.service.ts)."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.dp_service = DataPartitionService(db)
        self.coll = db["data_partition_users"]

    async def sync_bulk(self, bulk: List[dict], full_sync: bool = False, sync_group: Optional[str] = None) -> dict:
        """Port 1-1 từ syncBulk (data-partition-user.service.ts:L141-177)."""
        if full_sync and not sync_group:
            raise AppException(status_code=400, message="Sync Group empty", error="Bad Request")

        upserted_ids = []
        for item in bulk:
            user_id = item.get("userId")
            dp_code = item.get("dataPartitionCode")
            update_data = {k: v for k, v in item.items() if k not in ("userId", "dataPartitionCode")}
            if sync_group:
                update_data["syncGroup"] = sync_group

            res = await self.coll.find_one_and_update(
                {"userId": user_id, "dataPartitionCode": dp_code},
                {"$set": update_data},
                upsert=True,
                return_document=True,
            )
            if full_sync and res:
                upserted_ids.append(res["_id"])

        if full_sync and sync_group:
            await self.coll.delete_many({
                "syncGroup": sync_group,
                "_id": {"$nin": upserted_ids},
            })

        return {"success": True, "count": len(bulk)}

    async def get_dp_user_by_mode(
        self, data_partition_code: str, user_id: str, mode: str
    ) -> List[dict]:
        """Port 1-1 từ getDpUserByMode (data-partition-user.service.ts:L179-233)."""
        # Find DPUser
        dp_user = await self.coll.find_one({
            "dataPartitionCode": data_partition_code,
            "userId": user_id,
        })
        if not dp_user:
            return []

        dp = await self.dp_service.model.get_by_code(data_partition_code)
        if not dp:
            return []

        partitions = []
        mode_upper = mode.upper()
        if mode_upper == "ROOT_PATH":
            partitions = await self.dp_service.get_root_path(data_partition_code)
        elif mode_upper == "SUBTREE":
            partitions = await self.dp_service.get_subtree(data_partition_code)
        elif mode_upper == "NODE":
            partitions = [dp]

        partition_codes = [p["ma"] for p in partitions if "ma" in p]
        cursor = self.coll.find({"dataPartitionCode": {"$in": partition_codes}})
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results
