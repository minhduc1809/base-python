import enum

class NguoiTraLoi(str, enum.Enum):
    CA_NHAN = "CA_NHAN"
    BAN_CAN_SU = "BAN_CAN_SU"
    CO_VAN_HOC_TAP = "CO_VAN_HOC_TAP"
    PHONG_CTSV = "PHONG_CTSV"

class TrangThaiPhieuDiem(str, enum.Enum):
    CHUA_GUI = "CHUA_GUI"
    LUU = "LUU"
    DA_GUI = "DA_GUI"

class LoaiKhaoSat(str, enum.Enum):
    CHAM_DIEM_REN_LUYEN = "CHAM_DIEM_REN_LUYEN"
    SELF_ASSESSMENT_QUESTIONS = "SELF_ASSESSMENT_QUESTIONS"
    CUOC_THI = "CUOC_THI"
    TRAC_NGHIEM = "TRAC_NGHIEM"

class LoaiCauHoiKhaoSat(str, enum.Enum):
    MINH_CHUNG = "MINH_CHUNG"
    HE_THONG = "HE_THONG"
    SINGLE_CHOICE = "SINGLE_CHOICE"
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    TEXT = "TEXT"
