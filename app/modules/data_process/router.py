"""
Data Process Router - 2 endpoints: replace-domain/mongo và replace-domain/sql.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_mongo_db, get_db_session
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.data_process.service import DataProcessService

router = APIRouter(prefix="/data-process", tags=["data-process"])


class ReplaceDomainUrlDto(BaseModel):
    oldDomain: str
    newDomain: str
    skipTables: Optional[List[str]] = None


@router.post("/replace-domain/mongo")
async def replace_domain_mongo(
    dto: ReplaceDomainUrlDto,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    service = DataProcessService(mongo_db=db)
    return await service.replace_domain_url_mongo(dto.oldDomain, dto.newDomain, dto.skipTables)


@router.post("/replace-domain/sql")
async def replace_domain_sql(
    dto: ReplaceDomainUrlDto,
    current_user: User = Depends(get_current_user),
    sql_db: AsyncSession = Depends(get_db_session),
):
    service = DataProcessService(sql_db=sql_db)
    return await service.replace_domain_url_sql(dto.oldDomain, dto.newDomain, dto.skipTables)
