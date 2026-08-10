from app.common.base_framework.base_controller_factory import create_base_router, DPQueryScope

router = create_base_router(
    collection_name="don_form_dong",
    prefix="/don-form-dong",
    tags=["don-form-dong"],
    scope=DPQueryScope.SUBTREE,
)
