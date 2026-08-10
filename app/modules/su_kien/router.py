from app.common.base_framework.base_controller_factory import create_base_router, DPQueryScope

router = create_base_router(
    collection_name="su_kien",
    prefix="/su-kien",
    tags=["su-kien"],
    scope=DPQueryScope.NODE,
)
