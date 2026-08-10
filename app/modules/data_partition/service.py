from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.modules.data_partition.models import DataPartitionModel


class DataPartitionService:
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self.model = DataPartitionModel(db)

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
            # Filter out already visited nodes to prevent circular loops
            visited_codes = {s["ma"] for s in subtree}
            children = [c for c in raw_children if c["ma"] not in visited_codes]

        return subtree
