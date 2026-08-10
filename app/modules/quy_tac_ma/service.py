from datetime import datetime
from typing import Any, Dict, List, Optional
from redis.asyncio import Redis
from app.core.context import get_current_partition_code
from app.modules.quy_tac_ma.models import QuyTacMaModel


class QuyTacMaService:
    def __init__(self, redis: Redis, mongo_db=None):
        self.redis = redis
        self.model = QuyTacMaModel(mongo_db)

    async def get_ma(self, nguon: str, data: Dict[str, Any]) -> str:
        """Sinh mã theo cấu hình động từ MongoDB."""
        quy_tac = await self.model.get_by_nguon(nguon)
        if not quy_tac or "cauHinh" not in quy_tac:
            # Fallback nếu chưa có cấu hình DB
            return await self.generate_code(prefix=nguon.upper(), entity_name=nguon)

        parts: List[str] = []
        for cau_hinh in quy_tac["cauHinh"]:
            loai = cau_hinh.get("loai")
            if loai == "THUOC_TINH":
                prop = cau_hinh.get("thuocTinh")
                if prop and prop in data:
                    parts.append(str(data[prop]))
            elif loai == "HAM_SINH":
                ham_sinh = cau_hinh.get("hamSinh", "auto_seq")
                if ham_sinh == "date_yyyymmdd":
                    parts.append(datetime.now().strftime("%Y%m%d"))
                elif ham_sinh == "date_yyyy":
                    parts.append(datetime.now().strftime("%Y"))
                else:
                    padding = cau_hinh.get("padding", 5)
                    seq = await self._get_next_sequence(f"{nguon}:{ham_sinh}")
                    parts.append(str(seq).zfill(padding))
            elif loai == "CONSTANT":
                parts.append(str(cau_hinh.get("value", "")))

        return "".join(parts) if parts else await self.generate_code(prefix="KS", entity_name=nguon)

    async def _get_next_sequence(self, key_name: str) -> int:
        partition = get_current_partition_code() or "default"
        redis_key = f"seq:{partition}:{key_name}"
        next_seq = await self.redis.incr(redis_key)
        if next_seq == 1:
            await self.redis.expire(redis_key, 86400 * 365)
        return next_seq

    async def generate_code(
        self,
        prefix: str,
        entity_name: str,
        padding: int = 5,
        include_date: bool = True,
        date_format: str = "%Y%m%d",
    ) -> str:
        """Sinh mã tự động tăng cơ bản bằng Redis."""
        partition = get_current_partition_code() or "default"
        now = datetime.now()
        date_str = now.strftime(date_format) if include_date else ""

        redis_key = f"seq:{partition}:{entity_name}:{prefix}:{date_str}"
        next_seq = await self.redis.incr(redis_key)
        if next_seq == 1:
            await self.redis.expire(redis_key, 86400 * 2)

        padded_seq = str(next_seq).zfill(padding)
        if include_date:
            return f"{prefix}{date_str}{padded_seq}"
        return f"{prefix}{padded_seq}"
