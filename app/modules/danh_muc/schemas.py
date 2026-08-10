from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class DanhMucCreate(BaseModel):
    ma: str = Field(..., max_length=100, description="Mã danh mục")
    ten: str = Field(..., max_length=255, description="Tên danh mục")
    loai: str = Field(..., max_length=100, description="Loại danh mục")
    mo_ta: Optional[str] = Field(None, description="Mô tả danh mục")
    thu_tu: int = Field(0, description="Thứ tự hiển thị")
    trang_thai: bool = Field(True, description="Trạng thái kích hoạt")


class DanhMucUpdate(BaseModel):
    ten: Optional[str] = Field(None, max_length=255)
    loai: Optional[str] = Field(None, max_length=100)
    mo_ta: Optional[str] = None
    thu_tu: Optional[int] = None
    trang_thai: Optional[bool] = None


class DanhMucResponse(BaseModel):
    id: int
    ma: str
    ten: str
    loai: str
    mo_ta: Optional[str] = None
    thu_tu: int
    trang_thai: bool
    data_partition_code: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
