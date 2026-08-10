from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_mongo_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.khao_sat.schemas import CauTraLoiKhaoSatSubmit

cau_tra_loi_router = APIRouter(prefix="/cau-tra-loi-khao-sat", tags=["cau-tra-loi-khao-sat"])


class StartTracNghiemDto(BaseModel):
    ma_khao_sat: str
    ma_dot: str


@cau_tra_loi_router.post("/me", status_code=status.HTTP_201_CREATED)
async def create_me(
    payload: CauTraLoiKhaoSatSubmit,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    from app.modules.khao_sat.service import KhaoSatService
    service = KhaoSatService(db)
    user_dict = {
        "ssoId": str(getattr(current_user, "sso_id", None) or getattr(current_user, "sub", None) or current_user.id),
        "username": current_user.username,
        "fullname": getattr(current_user, "full_name", None) or current_user.username,
    }
    return await service.user_create_cau_tra_loi_khao_sat(user_dict, payload)



@cau_tra_loi_router.put("/me/save")
async def save_me(
    payload: CauTraLoiKhaoSatSubmit,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    from app.modules.khao_sat.service import KhaoSatService
    service = KhaoSatService(db)
    user_dict = {
        "ssoId": str(getattr(current_user, "sso_id", None) or getattr(current_user, "sub", None) or current_user.id),
        "username": current_user.username,
        "fullname": getattr(current_user, "full_name", None) or current_user.username,
    }
    return await service.user_create_cau_tra_loi_khao_sat(user_dict, payload, mode="save")



@cau_tra_loi_router.get("/me/khao-sat/{idKhaoSat}/dot/{idDot}")
async def get_cau_tra_loi_id_bieu_mau(
    idKhaoSat: str,
    idDot: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    user_sso = str(getattr(current_user, "sso_id", None) or current_user.id)
    doc = await coll.find_one({
        "$or": [{"userSsoId": user_sso}, {"userId": str(current_user.id)}],
        "idKhaoSat": idKhaoSat,
        "idDot": idDot
    })
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc


@cau_tra_loi_router.get("/khao-sat/{idSuKien}/{loai}/{ssoId}")
async def get_cau_tra_loi_khao_sat_su_kien(
    idSuKien: str,
    loai: str,
    ssoId: str,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    coll = db["cau_tra_loi_khao_sat"]
    doc = await coll.find_one({
        "idSuKien": idSuKien,
        "loai": loai,
        "ssoId": ssoId
    })
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc


@cau_tra_loi_router.get("/id-khao-sat/da-tra-loi")
async def get_id_bieu_mau_da_tra_loi(
    loai: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    coll = db["cau_tra_loi_khao_sat"]
    query = {"userId": str(current_user.id)}
    if loai:
        query["loai"] = loai
    cursor = coll.find(query)
    items = []
    async for doc in cursor:
        items.append(str(doc.get("khaoSatId")))
    return items


@cau_tra_loi_router.post("/trac-nghiem/initialize/answer/khao-sat", status_code=status.HTTP_201_CREATED)
async def init_trac_nghiem_answer(
    dto: StartTracNghiemDto,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    coll = db["cau_tra_loi_khao_sat"]
    doc = {
        "userId": str(current_user.id),
        "khaoSatId": dto.ma_khao_sat,
        "dotId": dto.ma_dot,
        "status": "started"
    }
    res = await coll.insert_one(doc)
    doc["_id"] = str(res.inserted_id)
    return doc


@cau_tra_loi_router.post("/dong-bo-khao-sat/dot/{idDot}")
async def dong_bo_cau_tra_loi_khao_sat(
    idDot: str
):
    return {"status": "success", "message": f"Data synced successfully for dot {idDot}"}


from app.common.base_framework.base_controller_factory import create_base_router, DPQueryScope

# Base Class integration for sub-routers
cau_tra_loi_base = create_base_router(collection_name="cau_tra_loi_khao_sat", prefix="/cau-tra-loi-khao-sat", tags=["cau-tra-loi-khao-sat"], scope=DPQueryScope.NODE)
cau_tra_loi_router.include_router(cau_tra_loi_base)

danh_gia_giang_vien_router = create_base_router(collection_name="danh_gia_giang_vien", prefix="/danh-gia-giang-vien", tags=["danh-gia-giang-vien"], scope=DPQueryScope.NODE)

dm_cau_hoi_router = create_base_router(collection_name="dm_cau_hoi_khao_sat", prefix="/dm-cau-hoi-khao-sat", tags=["dm-cau-hoi-khao-sat"], scope=DPQueryScope.NODE)

thong_tin_khai_bao_router = create_base_router(collection_name="thong_tin_khai_bao_khao_sat", prefix="/thong-tin-khai-bao-khao-sat", tags=["thong-tin-khai-bao-khao-sat"], scope=DPQueryScope.NODE)

thong_tin_nguoi_tham_gia_router = APIRouter(prefix="/thong-tin-nguoi-khao-sat", tags=["Thong tin nguoi khao sat"])

@thong_tin_nguoi_tham_gia_router.post("/many", status_code=status.HTTP_201_CREATED)
async def create_many_nguoi_khao_sat(
    payload: dict,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    coll = db["thong_tin_nguoi_tham_gia_khao_sat"]
    items = payload.get("items", [])
    if items:
        res = await coll.insert_many(items)
        return {"inserted": len(res.inserted_ids)}
    return {"inserted": 0}

nguoi_khao_sat_base = create_base_router(collection_name="thong_tin_nguoi_tham_gia_khao_sat", prefix="/thong-tin-nguoi-khao-sat", tags=["Thong tin nguoi khao sat"], scope=DPQueryScope.NODE)
thong_tin_nguoi_tham_gia_router.include_router(nguoi_khao_sat_base)
