from typing import List
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.exceptions import AppException
from app.core.context import set_current_user_id
from app.core.database import get_db_session
from app.core.security import decode_access_token
from app.modules.auth.models import User

security_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """Dependency lấy thông tin User hiện tại từ JWT Bearer token (Hỗ trợ cả Local JWT và Keycloak SSO JWT)."""
    token = credentials.credentials
    user = None

    # 1. Thử giải mã bằng Local JWT
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
    except Exception:
        pass

    # 2. Nếu thất bại, thử verify qua Keycloak SSO JWT
    if not user:
        from app.modules.sso.service import SsoService
        try:
            sso_service = SsoService(db)
            sso_payload = await sso_service.verify(f"Bearer {token}")
            user = await sso_service.init_user(sso_payload)
        except Exception:
            raise AppException(
                status_code=401, message="Token không hợp lệ hoặc đã hết hạn", error="Unauthorized"
            )

    if not user or not user.is_active:
        raise AppException(
            status_code=401, message="Người dùng không hoạt động", error="Unauthorized"
        )

    # Inject user_id vào ContextVar để AuditLogMiddleware có thể đọc được
    set_current_user_id(str(user.id))

    return user


def require_roles(allowed_roles: List[str]):
    """Dependency kiểm tra phân quyền người dùng."""

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.is_superuser:
            return current_user

        user_roles = [r.name.upper() for r in current_user.roles]
        if current_user.system_role:
            user_roles.append(current_user.system_role.upper())

        allowed_upper = [r.upper() for r in allowed_roles]
        has_role = any(role in user_roles for role in allowed_upper)

        if not has_role:
            raise AppException(
                status_code=403,
                message="Bạn không có quyền thực hiện thao tác này",
                error="Forbidden",
            )
        return current_user

    return role_checker
