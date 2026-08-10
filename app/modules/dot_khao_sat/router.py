from app.common.base_framework.base_controller_factory import create_base_router, DPQueryScope

# Migrated to Base Class with NODE partition scope matching NestJS DotKhaoSatController
router = create_base_router(
    collection_name="dot_khao_sat",
    prefix="/dot-khao-sat",
    tags=["dot-khao-sat"],
    scope=DPQueryScope.NODE,
)
