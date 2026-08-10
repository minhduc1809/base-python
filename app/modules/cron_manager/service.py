from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.modules.cron_manager.models import CronManagerModel


class CronManagerService:
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self.model = CronManagerModel(db)

    async def add_cron_job(self, name: str, cron_expression: str, target_url: str) -> Dict[str, Any]:
        """Port từ addCronJob (cron-manager.service.ts:L20-40)."""
        return await self.model.add_cron_job(name, cron_expression, target_url)

    async def delete_cron_job(self, job_id: str) -> bool:
        """Port từ deleteCronJob (cron-manager.service.ts:L45-60)."""
        return await self.model.delete_cron_job(job_id)

    async def list_cron_jobs(self) -> List[Dict[str, Any]]:
        """Port từ listCronJobs (cron-manager.service.ts:L65-75)."""
        return await self.model.list_cron_jobs()

    async def toggle_cron_job(self, job_id: str, enabled: bool) -> Optional[Dict[str, Any]]:
        """Port từ toggleCronJob (cron-manager.service.ts:L80-95)."""
        return await self.model.toggle_cron_job(job_id, enabled)
