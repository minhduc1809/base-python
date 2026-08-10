from typing import Any, Dict, List, Optional
from app.common.base_framework.base_import_service import BaseImportService
from app.core.security import hash_password


class UserImportService(BaseImportService):
    """Port 1-1 từ UserImportService trong NestJS (user-import.service.ts:L1-35)."""

    async def preprocess_import(
        self, rows: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Preprocess batch import rows for Users."""
        valid_rows = []
        for item in rows:
            row_data = item.get("row", item)
            # Standardize username & email
            if "username" in row_data:
                row_data["username"] = str(row_data["username"]).strip()
            valid_rows.append({"index": item.get("index", 0), "row": row_data})
        return {"rows": valid_rows, "context": context or {}}

    async def validate_and_transform_row_data(
        self, row_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Validate single row data for User import."""
        doc = row_data.get("row", {})
        errors = []
        if not doc.get("username"):
            errors.append("Tên đăng nhập không được để trống")
        if not doc.get("email"):
            errors.append("Email không được để trống")

        # Hash password if provided in excel
        if doc.get("password"):
            doc["hashed_password"] = hash_password(doc["password"])

        return {"doc": {"index": row_data.get("index", 0), "row": doc}, "errors": errors}
