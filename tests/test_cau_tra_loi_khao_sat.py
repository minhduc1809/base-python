import pytest
from unittest.mock import AsyncMock, MagicMock
from app.modules.khao_sat.service import KhaoSatService
from app.modules.khao_sat.schemas import CauTraLoiKhaoSatSubmit
from app.modules.khao_sat.constants import NguoiTraLoi, TrangThaiPhieuDiem


@pytest.mark.asyncio
async def test_first_time_submit_creates_record_and_updates_phieu_diem():
    db_mock = MagicMock()

    answers_coll = MagicMock()
    answers_coll.find_one = AsyncMock(return_value=None)  # No existing submission
    insert_res = MagicMock()
    insert_res.inserted_id = "ans_123"
    answers_coll.insert_one = AsyncMock(return_value=insert_res)

    phieu_diem_coll = MagicMock()
    phieu_diem_coll.update_one = AsyncMock()

    khao_sat_coll = MagicMock()
    khao_sat_coll.find_one = AsyncMock(return_value={"_id": "ks_1", "danhSachKhoi": []})

    db_mock.__getitem__.side_effect = lambda name: {
        "cau_tra_loi_khao_sat": answers_coll,
        "phieu_diem_ren_luyen": phieu_diem_coll,
        "khao_sat": khao_sat_coll,
        "dot_khao_sat": MagicMock()
    }.get(name, MagicMock())

    service = KhaoSatService(db_mock)

    user = {"ssoId": "user_sso_1", "username": "student1", "fullname": "Nguyen Van A"}
    dto = CauTraLoiKhaoSatSubmit(
        idKhaoSat="ks_1",
        idDotChamDiemRenLuyen="dot_123",
        ssoIdSinhVien="student_sso_1",
        nguoiTraLoi=NguoiTraLoi.CA_NHAN,
        trangThaiNopSV=TrangThaiPhieuDiem.DA_GUI,
        danhSachTraLoi=[{"idCauHoi": "q1", "traLoiText": "10"}]
    )

    res = await service.user_create_cau_tra_loi_khao_sat(user, dto)

    # Check 1: Record created with _id
    assert res["_id"] == "ans_123"
    assert res["userSsoId"] == "user_sso_1"
    assert res["ssoIdSinhVien"] == "student_sso_1"
    answers_coll.insert_one.assert_called_once()

    # Check 2: PhieuDiemRenLuyen status updated to DA_GUI
    phieu_diem_coll.update_one.assert_called_once_with(
        {"ssoId": "student_sso_1", "dotChamDiemId": "dot_123"},
        {"$set": {"trangThaiNopSV": TrangThaiPhieuDiem.DA_GUI}},
        upsert=True
    )


@pytest.mark.asyncio
async def test_duplicate_submit_updates_existing_record():
    db_mock = MagicMock()

    existing_doc = {
        "_id": "existing_ans_id",
        "ssoIdSinhVien": "student_sso_1",
        "userSsoId": "user_sso_1",
        "idDotChamDiemRenLuyen": "dot_123",
        "nguoiTraLoi": NguoiTraLoi.CO_VAN_HOC_TAP
    }

    answers_coll = MagicMock()
    answers_coll.find_one = AsyncMock(return_value=existing_doc)
    answers_coll.update_one = AsyncMock()

    phieu_diem_coll = MagicMock()
    phieu_diem_coll.update_one = AsyncMock()

    khao_sat_coll = MagicMock()
    khao_sat_coll.find_one = AsyncMock(return_value={
        "_id": "ks_1",
        "danhSachKhoi": [{
            "danhSachCauHoi": [
                {"_id": "q1", "loai": "TEXT"},
                {"_id": "q2", "loai": "TEXT"}
            ]
        }]
    })

    db_mock.__getitem__.side_effect = lambda name: {
        "cau_tra_loi_khao_sat": answers_coll,
        "phieu_diem_ren_luyen": phieu_diem_coll,
        "khao_sat": khao_sat_coll,
        "dot_khao_sat": MagicMock()
    }.get(name, MagicMock())

    service = KhaoSatService(db_mock)

    covan_user = {"ssoId": "covan_sso_1", "username": "covan1", "fullname": "Thay Co Van"}
    dto = CauTraLoiKhaoSatSubmit(
        idKhaoSat="ks_1",
        idDotChamDiemRenLuyen="dot_123",
        ssoIdSinhVien="student_sso_1",
        nguoiTraLoi=NguoiTraLoi.CO_VAN_HOC_TAP,
        trangThaiNopCoVan=TrangThaiPhieuDiem.DA_GUI,
        danhSachTraLoi=[
            {"idCauHoi": "q1", "traLoiText": "15"},
            {"idCauHoi": "q2", "traLoiText": "20"}
        ]
    )

    res = await service.user_create_cau_tra_loi_khao_sat(covan_user, dto)

    # Check 1: Record updated with existing ID
    assert res["_id"] == "existing_ans_id"
    # Check 2: Score calculated for CO_VAN_HOC_TAP with DA_GUI (15 + 20 = 35.0)
    assert res["diemPhongCTSV"] == 35.0
    answers_coll.update_one.assert_called_once()

    # Check 3: PhieuDiemRenLuyen status updated for CO_VAN_HOC_TAP
    phieu_diem_coll.update_one.assert_called_once_with(
        {"ssoId": "student_sso_1", "dotChamDiemId": "dot_123"},
        {"$set": {"trangThaiNopCoVan": TrangThaiPhieuDiem.DA_GUI}},
        upsert=True
    )
