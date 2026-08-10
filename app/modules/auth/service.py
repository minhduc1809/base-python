import time
import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.exceptions import AppException
from app.core.config import settings
from app.core.context import get_current_partition_code
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.modules.auth.models import User, Role
from app.modules.auth.models_mongo import AuthSessionService
from app.modules.auth.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.session_service = AuthSessionService()

    async def register(self, dto: RegisterRequest) -> User:
        partition_code = get_current_partition_code()
        # Check username duplicate
        stmt = select(User).where(User.username == dto.username)
        res = await self.db.execute(stmt)
        if res.scalar_one_or_none():
            raise AppException(status_code=400, message=f"Tài khoản '{dto.username}' đã tồn tại", error="Conflict")

        user = User(
            username=dto.username,
            email=dto.email,
            hashed_password=hash_password(dto.password) if dto.password else None,
            full_name=dto.full_name,
            data_partition_code=partition_code,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def login(
        self,
        dto: LoginRequest,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        origin: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> TokenResponse:
        stmt = select(User).where(User.username == dto.username)
        res = await self.db.execute(stmt)
        user = res.scalar_one_or_none()

        if not user or not user.hashed_password or not verify_password(dto.password, user.hashed_password):
            raise AppException(status_code=401, message="Tài khoản hoặc mật khẩu không chính xác", error="Unauthorized")

        if not user.is_active:
            raise AppException(status_code=403, message="Tài khoản đã bị khóa", error="Forbidden")

        jti = uuid.uuid4().hex
        exp = int(settings.JWT_REFRESH_EXP)

        # Create session in MongoDB
        session_doc = await self.session_service.create_session(
            user_id=user.id,
            jti=jti,
            exp=exp,
            ip=ip,
            user_agent=user_agent,
            origin=origin,
            platform=platform or dto.platform,
        )

        now_ts = int(time.time())
        access_exp_ts = now_ts + int(settings.JWT_EXP)
        refresh_exp_ts = now_ts + int(settings.JWT_REFRESH_EXP)

        roles = [r.name for r in user.roles]
        extra_claims = {
            "jti": jti,
            "sub": str(user.id),
            "auth": session_doc["_id"],
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "firstName": user.firstname,
            "lastName": user.lastname,
            "systemRole": user.system_role,
            "roles": roles,
            "platform": platform or dto.platform,
            "data_partition_code": user.data_partition_code,
        }

        access_token = create_access_token(subject=str(user.id), extra_claims=extra_claims)
        refresh_token = create_refresh_token(subject=str(user.id), extra_claims={"jti": jti, "auth": session_doc["_id"]})

        return TokenResponse(
            accessToken=access_token,
            refreshToken=refresh_token,
            accessExpireAt=access_exp_ts,
            refreshExpireAt=refresh_exp_ts,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.JWT_EXP,
        )

    async def logout(self, refresh_token_str: str) -> bool:
        """Revoke active session on logout."""
        try:
            payload = decode_refresh_token(refresh_token_str)
            jti = payload.get("jti")
            if jti:
                await self.session_service.revoke_session(jti)
                return True
        except Exception:
            pass
        raise AppException(status_code=401, message="Token không hợp lệ hoặc đã bị thu hồi", error="Unauthorized")

    async def refresh_tokens(self, refresh_token_str: str) -> TokenResponse:
        try:
            payload = decode_refresh_token(refresh_token_str)
            user_id = int(payload.get("sub"))
            jti = payload.get("jti")
        except Exception:
            raise AppException(status_code=401, message="Refresh token không hợp lệ hoặc đã hết hạn", error="Unauthorized")

        # Check session status in MongoDB
        if jti:
            session = await self.session_service.get_session(jti)
            if not session:
                raise AppException(status_code=401, message="Phiên làm việc đã bị hủy hoặc không tồn tại", error="Unauthorized")

        stmt = select(User).where(User.id == user_id)
        res = await self.db.execute(stmt)
        user = res.scalar_one_or_none()
        if not user or not user.is_active:
            raise AppException(status_code=401, message="Người dùng không hợp lệ", error="Unauthorized")

        new_jti = uuid.uuid4().hex
        exp = int(settings.JWT_REFRESH_EXP)

        # Invalidate old session, create new
        if jti:
            await self.session_service.revoke_session(jti)

        session_doc = await self.session_service.create_session(
            user_id=user.id,
            jti=new_jti,
            exp=exp,
        )

        now_ts = int(time.time())
        access_exp_ts = now_ts + int(settings.JWT_EXP)
        refresh_exp_ts = now_ts + int(settings.JWT_REFRESH_EXP)

        roles = [r.name for r in user.roles]
        extra_claims = {
            "jti": new_jti,
            "sub": str(user.id),
            "auth": session_doc["_id"],
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "firstName": user.firstname,
            "lastName": user.lastname,
            "systemRole": user.system_role,
            "roles": roles,
        }

        new_access_token = create_access_token(subject=str(user.id), extra_claims=extra_claims)
        new_refresh_token = create_refresh_token(subject=str(user.id), extra_claims={"jti": new_jti, "auth": session_doc["_id"]})

        return TokenResponse(
            accessToken=new_access_token,
            refreshToken=new_refresh_token,
            accessExpireAt=access_exp_ts,
            refreshExpireAt=refresh_exp_ts,
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.JWT_EXP,
        )

    async def change_password(self, user_id: int, dto: ChangePasswordRequest) -> bool:
        stmt = select(User).where(User.id == user_id)
        res = await self.db.execute(stmt)
        user = res.scalar_one_or_none()

        if not user or not user.hashed_password or not verify_password(dto.old_password, user.hashed_password):
            raise AppException(status_code=400, message="Mật khẩu cũ không chính xác", error="Bad Request")

        user.hashed_password = hash_password(dto.new_password)
        await self.db.flush()
        return True
