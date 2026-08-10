"""
Celery Tasks cho Audit Log.
Xóa audit log cũ quá 2 năm chạy định kỳ mỗi 12 giờ.
"""
import asyncio
from app.tasks.celery_app import celery_app


@celery_app.task(name="audit_log.clear_old_logs")
def clear_old_audit_logs(years: int = 2):
    """Xóa toàn bộ audit log cũ hơn {years} năm. Chạy async trong Celery worker."""
    async def _run():
        from app.core.database import get_mongo_db
        from app.modules.audit_log.service import AuditLogService
        db = get_mongo_db()
        service = AuditLogService(db)
        deleted = await service.clear_old_logs(years=years)
        return deleted

    return asyncio.get_event_loop().run_until_complete(_run())
