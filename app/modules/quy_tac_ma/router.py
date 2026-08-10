from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from redis.asyncio import Redis
from app.core.database import get_mongo_db, get_redis
from app.modules.quy_tac_ma.service import QuyTacMaService

router = APIRouter(prefix="/quy-tac-ma", tags=["quy-tac-ma"])


class GetMaRequest(BaseModel):
    nguon: str
    data: Optional[Dict[str, Any]] = {}


@router.post("/get-ma")
async def get_ma(
    dto: GetMaRequest,
    redis: Redis = Depends(get_redis),
    mongo_db=Depends(get_mongo_db),
):
    """Sinh mã tự động dựa trên cấu hình nguồn."""
    service = QuyTacMaService(redis=redis, mongo_db=mongo_db)
    ma = await service.get_ma(nguon=dto.nguon, data=dto.data)
    return {"ma": ma, "code": ma}


@router.post("/generate")
async def generate_code(
    prefix: str = Query("KS", description="Tiền tố mã"),
    entity_name: str = Query("khao_sat", description="Tên đối tượng sinh mã"),
    padding: int = Query(5, description="Độ dài chữ số tự tăng"),
    include_date: bool = Query(True, description="Kèm ngày tháng"),
    redis: Redis = Depends(get_redis),
):
    service = QuyTacMaService(redis)
    generated_code = await service.generate_code(
        prefix=prefix,
        entity_name=entity_name,
        padding=padding,
        include_date=include_date,
    )
    return {"code": generated_code}
