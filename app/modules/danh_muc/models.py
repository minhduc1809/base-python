from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from app.core.database import Base


class DanhMuc(Base):
    __tablename__ = "danh_muc"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ma = Column(String(100), nullable=False, unique=True, index=True)
    ten = Column(String(255), nullable=False)
    loai = Column(String(100), nullable=False, index=True)
    mo_ta = Column(Text, nullable=True)
    thu_tu = Column(Integer, default=0)
    trang_thai = Column(Boolean, default=True)
    data_partition_code = Column(String(100), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
