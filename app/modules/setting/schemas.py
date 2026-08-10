from typing import Optional
from pydantic import BaseModel


class SettingCreateOrUpdate(BaseModel):
    key: str
    value: Optional[str] = None
    description: Optional[str] = None


class SettingResponse(BaseModel):
    id: int
    key: str
    value: Optional[str] = None
    description: Optional[str] = None
