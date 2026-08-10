from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_mongo_db
from app.modules.cron_manager.service import CronManagerService

router = APIRouter(prefix="/cron-manager", tags=["cron-manager"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_cron_job(
    name: str,
    cron_expression: str,
    target_url: str,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    service = CronManagerService(db)
    return await service.add_cron_job(name, cron_expression, target_url)


@router.get("")
async def list_cron_jobs(
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    service = CronManagerService(db)
    return await service.list_cron_jobs()


@router.put("/{job_id}/toggle")
async def toggle_cron_job(
    job_id: str,
    enabled: bool,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    service = CronManagerService(db)
    res = await service.toggle_cron_job(job_id, enabled)
    if not res:
        raise HTTPException(status_code=404, detail="Cron job not found")
    return res


@router.delete("/{job_id}")
async def delete_cron_job(
    job_id: str,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    service = CronManagerService(db)
    success = await service.delete_cron_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Cron job not found")
    return {"success": True}
