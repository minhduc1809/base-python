"""
Auth Service - Đăng nhập, đăng xuất, làm mới token và quản lý phiên làm việc.
"""
import time
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import AppException
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    verify_password,
)
from app.modules.auth.models import User
from app.modules.auth.models_mongo import AuthSessionService
from app.modules.auth.schemas import (
    LoginRequest,
    TokenResponse,
)


class AuthService:
    """Service xử lý logic xác thực tài khoản và cấp JWT token."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.session_service = AuthSessionService()

    # ─── login (auth.service.ts:L49-62) ─────────────────────────────
    async def login(
        self,
        dto: LoginRequest,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        origin: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> TokenResponse:
        user = await self._validate_password(dto.username, dto.password)
        auth = await self._create_empty_auth(user, {
            "ip": ip,
            "userAgent": user_agent,
            "origin": origin,
            "platform": platform or getattr(dto, "platform", None),
        })
        access_token, refresh_token = await self._generate_tokens(user, auth)
        return self._get_login_info(access_token, refresh_token)

    # ─── logout (auth.service.ts:L64-71) ────────────────────────────
    async def logout(self, refresh_token_str: str):
        """Revoke auth bằng refresh token. Port 1-1 từ logout(dto: LogoutDto)."""
        invoke = await self._revoke_auth_by_refresh_token(refresh_token_str)
        if invoke:
            return
        else:
            raise AppException(status_code=401, message="error-unauthorized", error="Unauthorized")

    # ─── createEmptyAuth (auth.service.ts:L73-87) ───────────────────
    async def _create_empty_auth(self, user: User, data: dict) -> dict:
        """Tạo auth session trống trong MongoDB — port 1-1 từ createEmptyAuth."""
        jti = uuid.uuid4().hex
        doc = await self.session_service.create_session(
            user_id=user.id,
            jti=jti,
            exp=None,  # Sẽ set trong generateTokens
            ip=data.get("ip"),
            user_agent=data.get("userAgent"),
            origin=data.get("origin"),
            platform=data.get("platform"),
        )
        doc["jti"] = jti
        return doc

    # ─── generateTokens (auth.service.ts:L89-101) ──────────────────
    async def _generate_tokens(self, user: User, auth: dict) -> tuple:
        """Port 1-1 từ generateTokens(user, auth)."""
        if not user:
            raise AppException(status_code=401, message="Unauthorized", error="Unauthorized")
        refresh_exp = int(settings.JWT_REFRESH_EXP)
        if not auth.get("exp"):
            auth["exp"] = int(time.time()) + refresh_exp
        # Update auth record với exp
        await self.session_service.update_session(auth["_id"], {"exp": auth["exp"]})
        return await self._get_tokens(auth, user)

    # ─── getTokens (auth.service.ts:L103-146) ──────────────────────
    async def _get_tokens(self, auth: dict, user: User) -> tuple:
        """Port 1-1 từ private getTokens(auth, user)."""
        if not auth.get("jti") and not auth.get("exp"):
            raise AppException(status_code=400, message="Bad Request", error="Bad Request")

        # AccessPayload — port 1-1 từ auth.service.ts:L110-122
        access_payload = {
            "jti": auth["jti"],
            "sub": str(user.id),
            "auth": str(auth["_id"]),
            "id": str(auth["_id"]),
            "username": user.username,
            "email": user.email,
            "firstName": user.firstname,
            "lastName": user.lastname,
            "scope": None,
            "platform": auth.get("platform"),
            "systemRole": user.system_role,
        }

        # RefreshPayload — port 1-1 từ auth.service.ts:L123-135
        refresh_payload = {
            "jti": auth["jti"],
            "sub": str(user.id),
            "auth": str(auth["_id"]),
            "username": user.username,
            "email": user.email,
            "firstName": user.firstname,
            "lastName": user.lastname,
            "scope": None,
            "platform": auth.get("platform"),
            "systemRole": user.system_role,
            "exp": auth["exp"],
        }

        access_token = create_access_token(subject=str(user.id), extra_claims=access_payload)
        refresh_token = create_refresh_token(subject=str(user.id), extra_claims=refresh_payload)
        return access_token, refresh_token

    # ─── refreshTokens (auth.service.ts:L148-164) ──────────────────
    async def refresh_tokens(self, refresh_token_str: str) -> TokenResponse:
        """Port 1-1 từ refreshTokens(dto). 
        KHÔNG revoke+tạo session mới — giữ nguyên auth cũ, chỉ generate token mới."""
        payload = self._verify_refresh_token(refresh_token_str)
        auth_id = payload.get("auth")
        jti = payload.get("jti")
        # getOne({ _id: payload.auth, jti: payload.jti })
        auth = await self.session_service.get_session_by_id_and_jti(auth_id, jti)
        if auth:
            user_id = int(payload.get("sub"))
            stmt = select(User).where(User.id == user_id)
            res = await self.db.execute(stmt)
            user = res.scalar_one_or_none()
            if not user:
                raise AppException(status_code=401, message="error-unauthorized", error="Unauthorized")
            access_token, refresh_token = await self._generate_tokens(user, auth)
            return self._get_login_info(access_token, refresh_token)
        else:
            raise AppException(status_code=401, message="error-unauthorized", error="Unauthorized")

    # ─── getLoginInfo (auth.service.ts:L166-182) ────────────────────
    def _get_login_info(self, access_token: str, refresh_token: str) -> TokenResponse:
        """Port 1-1 từ private getLoginInfo."""
        import jwt as pyjwt
        access_payload = pyjwt.decode(access_token, options={"verify_signature": False})
        refresh_payload = pyjwt.decode(refresh_token, options={"verify_signature": False})
        return TokenResponse(
            accessToken=access_token,
            refreshToken=refresh_token,
            accessExpireAt=access_payload.get("exp"),
            refreshExpireAt=refresh_payload.get("exp"),
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.JWT_EXP,
        )

    # ─── revokeAuthByRefreshToken (auth.service.ts:L184-190) ───────
    async def _revoke_auth_by_refresh_token(self, refresh_token_str: str) -> bool:
        """Port 1-1 từ revokeAuthByRefreshToken. deleteOne({_id, jti})."""
        payload = self._verify_refresh_token(refresh_token_str)
        auth_id = payload.get("auth")
        jti = payload.get("jti")
        return await self.session_service.delete_session(auth_id, jti)

    # ─── verifyRefreshToken (auth.service.ts:L192-208) ──────────────
    def _verify_refresh_token(self, refresh_token_str: str) -> dict:
        """Port 1-1 từ private verifyRefreshToken."""
        try:
            payload = decode_refresh_token(refresh_token_str)
            return payload
        except Exception as err:
            print(f"verifyRefreshToken error: {err}")
            raise AppException(status_code=401, message="error-unauthorized", error="Unauthorized")

    # ─── validatePassword (auth.service.ts:L210-222) ────────────────
    async def _validate_password(self, username: str, password: str) -> User:
        """Port 1-1 từ private validatePassword.
        getOne({ username }, { enableDataPartition: false })."""
        stmt = select(User).where(User.username == username)
        res = await self.db.execute(stmt)
        user = res.scalar_one_or_none()
        if user:
            match = verify_password(password, user.hashed_password)
            if match:
                return user
        raise AppException(status_code=401, message="error-unauthorized", error="Unauthorized")
