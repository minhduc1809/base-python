from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db_session, get_redis

router = APIRouter(prefix="/sso", tags=["sso"])


@router.get("/config")
async def get_sso_config():
    """Trả về cấu hình SSO client-side (JWKS URI, authority, client_id)."""
    return {
        "jwks_uri": settings.SSO_JWKS_URI or (
            f"{settings.KEYCLOAK_AUTHORITY}/protocol/openid-connect/certs"
            if settings.KEYCLOAK_AUTHORITY else None
        ),
        "authority": settings.KEYCLOAK_AUTHORITY,
        "client_id": settings.KEYCLOAK_CLIENT_ID,
    }


@router.post("/login")
async def sso_login(
    request_body: dict,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Xác thực Bearer Token từ Keycloak SSO và khởi tạo User nếu chưa tồn tại.
    Nhận body: { "access_token": "Bearer ..." }
    """
    from app.modules.sso.service import SsoService
    from app.core.security import create_access_token, create_refresh_token

    bearer_token = request_body.get("access_token") or request_body.get("bearer_token")
    if not bearer_token:
        from app.common.exceptions import AppException
        raise AppException(status_code=400, message="Thiếu trường access_token", error="Bad Request")

    redis = await get_redis()
    sso_service = SsoService(db=db, redis=redis)

    # Verify Keycloak token
    payload = await sso_service.verify(bearer_token)

    # Auto init user in PostgreSQL
    user = await sso_service.init_user(payload)

    # Issue our own JWT for the internal system
    roles = [r.name for r in user.roles]
    extra_claims = {
        "user_id": user.id,
        "username": user.username,
        "roles": roles,
        "system_role": user.system_role,
        "sso_id": user.sso_id,
        "data_partition_code": user.data_partition_code,
    }
    access_token = create_access_token(subject=str(user.id), extra_claims=extra_claims)
    refresh_token = create_refresh_token(subject=str(user.id))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_EXP,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "sso_id": user.sso_id,
            "system_role": user.system_role,
        },
    }
