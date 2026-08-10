import time
import uuid
from typing import Callable
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.context import (
    set_current_partition_code,
    set_current_request_id,
    set_current_user_id,
)
from app.core.logging import logger


class DataPartitionMiddleware(BaseHTTPMiddleware):
    """Middleware tự động trích xuất x-data-partition-code và x-request-id từ Request Header."""

    async def dispatch(self, request: Request, call_next):
        # Trích xuất data-partition-code từ header
        partition_code = request.headers.get("x-data-partition-code")
        set_current_partition_code(partition_code)

        # Trích xuất hoặc khởi tạo request-id
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        set_current_request_id(request_id)

        start_time = time.time()

        response = await call_next(request)

        process_time_ms = round((time.time() - start_time) * 1000, 2)
        response.headers["x-request-id"] = request_id
        if partition_code:
            response.headers["x-data-partition-code"] = partition_code
        response.headers["x-response-time"] = f"{process_time_ms}ms"

        logger.info(
            "HTTP Request Processed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=process_time_ms,
            partition_code=partition_code,
            request_id=request_id,
        )

        return response


class AuditLogMiddleware(BaseHTTPMiddleware):
    """
    Middleware tự động ghi Audit Log mọi request HTTP vào MongoDB.
    Chỉ ghi các request đã xác thực (Authorization header có mặt).
    """

    # Các path không cần audit log (health, docs, static)
    SKIP_PATHS = {"/", "/health", "/health/ping"}
    SKIP_PREFIXES = ("/api/openapi", "/api/redoc", "/openapi.json", "/favicon")

    async def dispatch(self, request: Request, call_next):
        # Bỏ qua các path không cần thiết
        path = request.url.path
        if path in self.SKIP_PATHS or any(path.startswith(p) for p in self.SKIP_PREFIXES):
            return await call_next(request)

        # Chỉ audit log các request CÓ Authorization header
        has_auth = "authorization" in request.headers

        start_time = time.time()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as exc:
            raise
        finally:
            if has_auth:
                process_time_ms = round((time.time() - start_time) * 1000, 2)
                try:
                    from app.core.context import get_current_partition_code, get_current_user_id
                    from app.core.database import get_mongo_db
                    from app.modules.audit_log.service import AuditLogService

                    db = get_mongo_db()
                    service = AuditLogService(db)
                    await service.log_action(
                        action=f"{request.method} {path}",
                        module=path.split("/")[1] if "/" in path else path,
                        ip=request.client.host if request.client else None,
                        user_agent=request.headers.get("user-agent"),
                        request_type="http",
                        user_id=get_current_user_id(),
                        details={
                            "method": request.method,
                            "path": path,
                            "status_code": status_code,
                            "duration_ms": process_time_ms,
                            "query_params": str(request.query_params),
                        },
                    )
                except Exception as e:
                    # Never let audit log failure block request processing
                    logger.warn("AuditLogMiddleware: Failed to write audit log", error=str(e))
