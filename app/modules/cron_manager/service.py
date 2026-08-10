"""
Cron Manager Service - Quản lý tiến trình lập lịch (Cron Jobs).
"""
import os
from typing import Any, Dict, List, Optional
from redis.asyncio import Redis
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.core.database import get_redis
from app.core.logging import logger
from app.modules.cron_manager.models import CronManagerModel


class CronManagerService:
    """Service lập lịch và quản lý cron job."""

    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None, redis: Optional[Redis] = None):
        self.model = CronManagerModel(db)
        self.redis = redis

    async def _get_redis(self) -> Redis:
        if not self.redis:
            self.redis = await get_redis()
        return self.redis

    def is_cron_server(self) -> bool:
        """Port 1-1 từ private isCronServer(). Check config server.cron (ENABLE_CRON)."""
        return getattr(settings, "ENABLE_CRON", True)

    async def is_cron_leader(self, class_name: str, function_name: str) -> bool:
        """Port 1-1 từ isCronLeader (cron-manager.service.ts:L25-45).
        Dùng Redis set(key, process_pid, ex=32, nx=True) để bầu chọn cron leader.
        """
        if self.is_cron_server():
            try:
                redis = await self._get_redis()
                cron_name = f"{class_name}.{function_name}"
                pid = os.getpid()
                acquired = await redis.set(cron_name, pid, ex=32, nx=True)
                return bool(acquired)
            except Exception as err:
                logger.error("Error cron leader acquire", error=str(err))
                return False
        return False

    async def add_cron_job(self, name: str, cron_expression: str, target_url: str) -> Dict[str, Any]:
        """Port từ addCronJob."""
        return await self.model.add_cron_job(name, cron_expression, target_url)

    async def delete_cron_job(self, job_id: str) -> bool:
        """Port từ deleteCronJob."""
        return await self.model.delete_cron_job(job_id)

    async def list_cron_jobs(self) -> List[Dict[str, Any]]:
        """Port từ listCronJobs."""
        return await self.model.list_cron_jobs()

    async def toggle_cron_job(self, job_id: str, enabled: bool) -> Optional[Dict[str, Any]]:
        """Port từ toggleCronJob."""
        return await self.model.toggle_cron_job(job_id, enabled)
