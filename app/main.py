import os
import sys

# Ensure root python-backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contextlib import asynccontextmanager
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.common.exceptions import (
    AppException,
    app_exception_handler,
    global_exception_handler,
)
from app.common.middleware import AuditLogMiddleware, DataPartitionMiddleware
from app.core.config import settings
from app.core.database import close_databases, init_databases
from app.core.logging import logger, setup_logging

# All Module Routers
from app.modules.audit_log.router import router as audit_log_router
from app.modules.auth.router import router as auth_router
from app.modules.common_provider.router import router as common_provider_router
from app.modules.core.router import router as core_router
from app.modules.cron_manager.router import router as cron_manager_router
from app.modules.danh_muc.router import router as danh_muc_router
from app.modules.data_partition.router import router as data_partition_router
from app.modules.data_partition.data_partition_user_router import router as data_partition_user_router
from app.modules.data_process.router import router as data_process_router
from app.modules.diem_ren_luyen.router import router as diem_ren_luyen_router
from app.modules.dot_khao_sat.router import router as dot_khao_sat_router
from app.modules.file.router import router as file_router
from app.modules.form_dong.router import router as form_dong_router
from app.modules.form_dong.don_form_dong_router import router as don_form_dong_router
from app.modules.health.router import router as health_router
from app.modules.import_session.router import router as import_session_router
from app.modules.increment.router import router as increment_router
from app.modules.internal_http.router import router as internal_http_router
from app.modules.ke_hoach_hoat_dong.router import router as ke_hoach_hoat_dong_router
from app.modules.khao_sat.router import router as khao_sat_router
from app.modules.khao_sat.sub_routers import (
    cau_tra_loi_router,
    danh_gia_giang_vien_router,
    dm_cau_hoi_router,
    thong_tin_khai_bao_router,
    thong_tin_nguoi_tham_gia_router,
)
from app.modules.logging.router import router as logging_router
from app.modules.microservice.router import router as microservice_router
from app.modules.minio.router import router as minio_router
from app.modules.notification.router import router as notification_router
from app.modules.one_signal.router import router as one_signal_router
from app.modules.quy_tac_ma.router import router as quy_tac_ma_router
from app.modules.redis.router import router as redis_router
from app.modules.repository.router import router as repository_router
from app.modules.setting.router import router as setting_router
from app.modules.sso.router import router as sso_router
from app.modules.su_kien.router import router as su_kien_router
from app.modules.topic.router import router as topic_router
from app.modules.user.router import router as user_router


# App level timestamp controller matching NestJS AppController
app_router = APIRouter(prefix="/app", tags=["App"])

@app_router.get("/timestamp")
async def get_timestamp():
    import time
    return int(time.time() * 1000)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info("Starting Python FastAPI Backend...", env=settings.SERVER_ENV)
    await init_databases()

    # OnApplicationBootstrap init
    try:
        from app.core.database import AsyncSessionLocal, get_mongo_db
        from app.modules.user.service import UserService
        async with AsyncSessionLocal() as db:
            mongo_db = get_mongo_db()
            user_svc = UserService(db, mongo_db)
            await user_svc.on_application_bootstrap()
            await db.commit()
    except Exception as e:
        logger.error("Failed to run on_application_bootstrap", error=str(e))

    yield
    # Shutdown
    logger.info("Shutting down Python FastAPI Backend...")
    await close_databases()


app = FastAPI(
    title="AISoft Backend",
    description="API Documentation for AISoft Backend",
    version="1.0.0",
    docs_url=f"/{settings.SERVER_DOCUMENT_PATH}",
    redoc_url=f"/{settings.SERVER_DOCUMENT_PATH}/redoc",
    openapi_url=f"/{settings.SERVER_DOCUMENT_PATH}/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Middlewares (order matters: added last = executed first for request)
app.add_middleware(AuditLogMiddleware)
app.add_middleware(DataPartitionMiddleware)

# Custom Exception Handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Register All Module Routers
app.include_router(app_router)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(setting_router)
app.include_router(danh_muc_router)
app.include_router(form_dong_router)
app.include_router(don_form_dong_router)
app.include_router(khao_sat_router)
app.include_router(dot_khao_sat_router)
app.include_router(cau_tra_loi_router)
app.include_router(danh_gia_giang_vien_router)
app.include_router(dm_cau_hoi_router)
app.include_router(thong_tin_khai_bao_router)
app.include_router(thong_tin_nguoi_tham_gia_router)
app.include_router(quy_tac_ma_router)
app.include_router(increment_router)
app.include_router(file_router)
app.include_router(minio_router)
app.include_router(audit_log_router)
app.include_router(cron_manager_router)
app.include_router(import_session_router)
app.include_router(notification_router)
app.include_router(one_signal_router)
app.include_router(topic_router)
app.include_router(data_partition_router)
app.include_router(data_partition_user_router)
app.include_router(data_process_router)
app.include_router(diem_ren_luyen_router)
app.include_router(ke_hoach_hoat_dong_router)
app.include_router(sso_router)
app.include_router(microservice_router)
app.include_router(internal_http_router)
app.include_router(common_provider_router)
app.include_router(core_router)
app.include_router(logging_router)
app.include_router(redis_router)
app.include_router(repository_router)
app.include_router(su_kien_router)


@app.get("/")
async def root():
    return {
        "name": "AISoft Backend API (Python Complete Parity)",
        "status": "online",
        "docs": f"{settings.SERVER_ADDRESS}/{settings.SERVER_DOCUMENT_PATH}",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.SERVER_ENV == "development",
    )
