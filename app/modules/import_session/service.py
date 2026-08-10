import io
from typing import Any, Dict, List, Optional
import openpyxl
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.modules.import_session.models import ImportSessionModel


class ImportSessionService:
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self.model = ImportSessionModel(db)

    async def create_import_session(self, module_name: str, total_records: int = 0) -> Dict[str, Any]:
        """Khởi tạo phiên import dữ liệu."""
        return await self.model.create_session(module_name=module_name, total_records=total_records)

    async def get_import_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin tiến trình phiên import."""
        return await self.model.get_by_id(session_id)

    async def update_import_session_status(
        self, session_id: str, status: str, processed: int = 0, error_logs: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """Cập nhật trạng thái tiến trình phiên import."""
        return await self.model.update_status(session_id, status=status, processed=processed, error_logs=error_logs)

    async def export_error_excel(self, session_id: str) -> bytes:
        """Xuất file Excel chứa chi tiết các dòng bị lỗi khi import."""
        session = await self.get_import_session(session_id)
        if not session:
            raise ValueError("Phiên import không tồn tại")

        error_logs = session.get("error_logs", [])
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Errors"

        ws.append(["Dòng", "Dữ liệu", "Lỗi chi tiết"])
        for err in error_logs:
            ws.append([
                err.get("index", ""),
                str(err.get("row", "")),
                "; ".join(err.get("rowErrors", [])) if isinstance(err.get("rowErrors"), list) else str(err.get("rowErrors", "")),
            ])

        output = io.BytesIO()
        wb.save(output)
        return output.getvalue()
