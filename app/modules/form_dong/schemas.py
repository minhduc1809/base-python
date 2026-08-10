from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FormDongCreate(BaseModel):
    ma_form: str = Field(..., description="Mã cấu hình form")
    ten_form: str = Field(..., description="Tên cấu hình form")
    fields: List[Dict[str, Any]] = Field(default_factory=list, description="Danh sách các trường động")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Cấu hình mở rộng")


class FormDongResponseSubmission(BaseModel):
    ma_form: str
    data: Dict[str, Any] = Field(..., description="Dữ liệu trả lời form động (dict tự do)")
    metadata: Optional[Dict[str, Any]] = None
