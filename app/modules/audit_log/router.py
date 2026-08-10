from typing import Optional
from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_mongo_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.audit_log.service import AuditLogService
from app.common.base_framework.base_controller_factory import create_base_router, DPQueryScope

# Instantiate Base Class Router with WRITE methods disabled (security protection)
router = create_base_router(
    collection_name="audit_logs",
    prefix="/audit-log",
    tags=["Audit log"],
    scope=DPQueryScope.GLOBAL,
    disabled_methods={"create", "updateById", "deleteById"},
)


@router.get("/page/me")
async def list_my_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Lấy danh sách Audit log của chính người dùng hiện tại."""
    service = AuditLogService(db)
    return await service.get_logs_for_user(user_id=str(current_user.id), limit=limit)


@router.delete("/expired")
async def delete_expired_logs(
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """Xóa tất cả các log đã cũ/hết hạn (khớp AuditLogInternalController.deleteExpired)."""
    import datetime
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=2*365)
    res = await db["audit_logs"].delete_many({"created_at": {"$lt": cutoff}})
    return {"deleted": res.deleted_count}
