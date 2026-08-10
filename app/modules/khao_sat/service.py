from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.context import get_current_partition_code
from app.modules.khao_sat.constants import NguoiTraLoi, TrangThaiPhieuDiem, LoaiKhaoSat, LoaiCauHoiKhaoSat
from app.modules.khao_sat.schemas import CauTraLoiKhaoSatSubmit, DotKhaoSatCreate


class KhaoSatService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.dot_collection = db["dot_khao_sat"]
        self.khao_sat_collection = db["khao_sat"]
        self.answers_collection = db["cau_tra_loi_khao_sat"]
        self.phieu_diem_collection = db["phieu_diem_ren_luyen"]

    async def create_dot_khao_sat(self, dto: DotKhaoSatCreate) -> Dict[str, Any]:
        partition_code = get_current_partition_code()
        now = datetime.now(timezone.utc)
        doc = {
            "ten_dot": dto.ten_dot,
            "tenDot": dto.ten_dot,
            "ma_dot": dto.ma_dot,
            "maDot": dto.ma_dot,
            "tu_ngay": dto.tu_ngay,
            "tuNgay": dto.tu_ngay,
            "den_ngay": dto.den_ngay,
            "denNgay": dto.den_ngay,
            "mo_ta": dto.mo_ta,
            "moTa": dto.mo_ta,
            "data_partition_code": partition_code,
            "dataPartitionCode": partition_code,
            "created_at": now,
            "createdAt": now,
        }
        res = await self.dot_collection.insert_one(doc)
        doc["_id"] = str(res.inserted_id)
        return doc

    async def list_dot_khao_sat(self) -> List[Dict[str, Any]]:
        partition_code = get_current_partition_code()
        query = {}
        if partition_code:
            query = {"$or": [{"data_partition_code": partition_code}, {"dataPartitionCode": partition_code}]}
        cursor = self.dot_collection.find(query).sort("createdAt", -1)
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results

    async def user_create_cau_tra_loi_khao_sat(
        self, user: Dict[str, Any], dto: CauTraLoiKhaoSatSubmit
    ) -> Dict[str, Any]:
        """
        Port 1-1 từ userCreate trong NestJS (cau-tra-loi-khao-sat.service.ts:L389-537).
        Bao gồm:
        - Tính điểm diemPhongCTSV / trắc nghiệm
        - Chống trùng (checkExist)
        - Cập nhật PhieuDiemRenLuyen
        """
        user_sso_id = user.get("ssoId") or user.get("sub") or user.get("id")
        user_code = user.get("username") or user.get("userCode")
        ho_ten = user.get("fullname") or " ".join(filter(None, [user.get("lastname"), user.get("firstname")]))

        # Lấy thông tin khảo sát nếu có
        khao_sat = None
        if dto.idKhaoSat:
            try:
                khao_sat = await self.khao_sat_collection.find_one({"_id": ObjectId(dto.idKhaoSat)})
            except Exception:
                khao_sat = await self.khao_sat_collection.find_one({"_id": dto.idKhaoSat})

        doc_dict = dto.model_dump(exclude_none=True)
        doc_dict.update({
            "userSsoId": user_sso_id,
            "userCode": user_code,
            "hoTen": ho_ten,
            "vaiTro": dto.nguoiTraLoi,
            "answered": True,
            "dataPartitionCode": get_current_partition_code(),
        })

        # 1. Tính điểm phòng CTSV nếu trangThaiNopCoVan == DA_GUI (L455-473)
        if dto.trangThaiNopCoVan == TrangThaiPhieuDiem.DA_GUI:
            doc_dict["diemPhongCTSV"] = 0.0
            list_id = []
            if khao_sat and "danhSachKhoi" in khao_sat:
                for khoi in khao_sat.get("danhSachKhoi", []):
                    for cau_hoi in khoi.get("danhSachCauHoi", []):
                        c_loai = cau_hoi.get("loai")
                        if c_loai not in [LoaiCauHoiKhaoSat.MINH_CHUNG, LoaiCauHoiKhaoSat.HE_THONG]:
                            list_id.append(str(cau_hoi.get("_id") or cau_hoi.get("id")))

            for tra_loi in dto.danhSachTraLoi:
                c_id = str(tra_loi.get("idCauHoi"))
                if not list_id or c_id in list_id:
                    try:
                        diem_val = float(tra_loi.get("traLoiText") or 0)
                        doc_dict["diemPhongCTSV"] += diem_val
                    except (ValueError, TypeError):
                        pass

        # 2. Check exist chống trùng (L490-495)
        check_exist_query = {
            "ssoIdSinhVien": dto.ssoIdSinhVien,
            "userSsoId": user_sso_id,
            "idDotChamDiemRenLuyen": dto.idDotChamDiemRenLuyen,
            "nguoiTraLoi": dto.nguoiTraLoi,
        }
        check_exist = await self.answers_collection.find_one(check_exist_query)

        # 3. Helper cập nhật PhieuDiemRenLuyen (L496-520)
        async def update_trang_thai():
            if not dto.ssoIdSinhVien or not dto.idDotChamDiemRenLuyen:
                return

            filter_pd = {
                "ssoId": dto.ssoIdSinhVien,
                "dotChamDiemId": dto.idDotChamDiemRenLuyen,
            }
            update_data = {}
            if dto.nguoiTraLoi == NguoiTraLoi.CA_NHAN and dto.trangThaiNopSV:
                update_data["trangThaiNopSV"] = dto.trangThaiNopSV
            elif dto.nguoiTraLoi == NguoiTraLoi.BAN_CAN_SU and dto.trangThaiNopBCS:
                update_data["trangThaiNopBCS"] = dto.trangThaiNopBCS
            elif dto.nguoiTraLoi == NguoiTraLoi.CO_VAN_HOC_TAP and dto.trangThaiNopCoVan:
                update_data["trangThaiNopCoVan"] = dto.trangThaiNopCoVan
            elif dto.nguoiTraLoi == NguoiTraLoi.PHONG_CTSV and dto.trangThaiPhongCTSV:
                update_data["trangThaiPhongCTSV"] = dto.trangThaiPhongCTSV

            if update_data:
                await self.phieu_diem_collection.update_one(
                    filter_pd,
                    {"$set": update_data},
                    upsert=True
                )

        now = datetime.now(timezone.utc)
        doc_dict["updatedAt"] = now

        if not check_exist:
            doc_dict["createdAt"] = now
            res = await self.answers_collection.insert_one(doc_dict)
            doc_dict["_id"] = str(res.inserted_id)
        else:
            await self.answers_collection.update_one(
                {"_id": check_exist["_id"]},
                {"$set": doc_dict}
            )
            doc_dict["_id"] = str(check_exist["_id"])

        await update_trang_thai()
        return doc_dict

    async def submit_answers(
        self, dto: CauTraLoiKhaoSatSubmit, user: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Wrapper method cho submit answers, ủy quyền sang user_create_cau_tra_loi_khao_sat."""
        if user is None:
            user = {"ssoId": dto.user_id, "username": dto.user_id}
        return await self.user_create_cau_tra_loi_khao_sat(user, dto)
