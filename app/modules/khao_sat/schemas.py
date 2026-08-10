from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.modules.khao_sat.constants import NguoiTraLoi, TrangThaiPhieuDiem


class DotKhaoSatCreate(BaseModel):
    ten_dot: str = Field(..., description="Tên đợt khảo sát")
    ma_dot: str = Field(..., description="Mã đợt khảo sát")
    tu_ngay: Optional[datetime] = None
    den_ngay: Optional[datetime] = None
    mo_ta: Optional[str] = None


class CauHoiKhaoSatCreate(BaseModel):
    ma_cau_hoi: str
    noi_dung: str
    loai_cau_hoi: str  # SINGLE_CHOICE, MULTIPLE_CHOICE, TEXT...
    lua_chon: List[Dict[str, Any]] = Field(default_factory=list)


class NoiDungTraLoiDto(BaseModel):
    idCauHoi: str
    traLoiText: Optional[str] = None
    listLuaChon: Optional[List[str]] = Field(default_factory=list)
    listLuaChonBang: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    correct: Optional[bool] = None
    diem: Optional[float] = 0.0


class CauTraLoiKhaoSatSubmit(BaseModel):
    idKhaoSat: str
    idDot: Optional[str] = None
    idDotChamDiemRenLuyen: Optional[str] = None
    ssoIdSinhVien: Optional[str] = None
    nguoiTraLoi: Optional[NguoiTraLoi] = None
    danhSachTraLoi: List[Dict[str, Any]] = Field(default_factory=list)
    trangThaiNopSV: Optional[TrangThaiPhieuDiem] = None
    trangThaiNopBCS: Optional[TrangThaiPhieuDiem] = None
    trangThaiNopCoVan: Optional[TrangThaiPhieuDiem] = None
    trangThaiPhongCTSV: Optional[TrangThaiPhieuDiem] = None
    diemPhongCTSV: Optional[float] = None
    # Backward compatibility fields
    ma_dot: Optional[str] = None
    user_id: Optional[str] = None
    answers: Optional[List[Dict[str, Any]]] = None
