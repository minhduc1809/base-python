from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_mongo_db
from app.common.base_framework.base_controller_factory import create_base_router, DPQueryScope

router = create_base_router(
    collection_name="data_partition_users",
    prefix="/data-partition-user",
    tags=["data-partition - user"],
    scope=DPQueryScope.GLOBAL,
)


@router.post("/sync/bulk", status_code=status.HTTP_201_CREATED)
async def sync_bulk(
    payload: dict,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Đồng bộ hàng loạt liên kết phân vùng dữ liệu người dùng (khớp DataPartitionUserInternalController.syncBulk)."""
    coll = db["data_partition_users"]
    items = payload.get("items", [])
    if items:
        for item in items:
            item.pop("_id", None)
            user_val = item.get("user")
            dp_val = item.get("dataPartition")
            if user_val and dp_val:
                await coll.find_one_and_update(
                    {"user": user_val, "dataPartition": dp_val},
                    {"$set": item},
                    upsert=True,
                )
        return {"status": "success", "synced": len(items)}
    return {"status": "success", "synced": 0}
