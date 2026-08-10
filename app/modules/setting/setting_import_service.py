from typing import Any, Dict, List, Optional
from app.common.base_framework.base_import_service import BaseImportService


class SettingImportService(BaseImportService):
    """Import service xử lý nhập dữ liệu cấu hình từ Excel."""

    async def preprocess_import(
        self, rows: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Preprocess batch import rows for Settings."""
        valid_rows = []
        for item in rows:
            row_data = item.get("row", item)
            if "key" in row_data:
                row_data["key"] = str(row_data["key"]).strip()
            valid_rows.append({"index": item.get("index", 0), "row": row_data})
        return {"rows": valid_rows, "context": context or {}}

    async def validate_and_transform_row_data(
        self, row_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Validate single row data for Setting import."""
        doc = row_data.get("row", {})
        errors = []
        if not doc.get("key"):
            errors.append("Mã Setting Key không được để trống")
        return {"doc": {"index": row_data.get("index", 0), "row": doc}, "errors": errors}
