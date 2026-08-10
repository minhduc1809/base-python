import json
from typing import Any, Dict, Optional
import httpx
import jwt
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.exceptions import AppException
from app.core.config import settings
from app.core.database import get_redis
from app.core.logging import logger
from app.modules.auth.models import User


class SsoService:
    JWKS_CERTS_KEY = "jwts:certs"

    def __init__(self, db: AsyncSession, redis: Optional[Redis] = None):
        self.db = db
        self.redis = redis

    async def get_redis_client(self) -> Redis:
        if not self.redis:
            self.redis = await get_redis()
        return self.redis

    async def get_certs(self) -> Dict[str, Any]:
        """Fetch and cache Keycloak JWKS certificates in Redis (TTL 4 seconds)."""
        redis = await self.get_redis_client()
        certs_str = await redis.get(self.JWKS_CERTS_KEY)

        if certs_str:
            try:
                return json.loads(certs_str)
            except Exception:
                pass

        jwks_uri = getattr(settings, "SSO_JWKS_URI", None) or (
            f"{settings.KEYCLOAK_AUTHORITY}/protocol/openid-connect/certs" if settings.KEYCLOAK_AUTHORITY else None
        )
        if not jwks_uri:
            raise AppException(status_code=500, message="SSO JWKS URI không được cấu hình", error="Internal Server Error")

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(jwks_uri, timeout=10.0)
                if resp.status_code == 200:
                    certs = resp.json()
                    await redis.set(self.JWKS_CERTS_KEY, json.dumps(certs), ex=4)
                    return certs
        except Exception as e:
            logger.error("Failed to fetch Keycloak JWKS certs", error=str(e))
            raise AppException(status_code=500, message="Không thể kết nối SSO Identity Provider", error="Internal Server Error")

    async def verify(self, bearer_token: str) -> Dict[str, Any]:
        """Verify Keycloak Bearer Token using PyJWT and JWKS."""
        if not bearer_token or not bearer_token.lower().startswith("bearer "):
            raise AppException(status_code=401, message="Header Authorization không đúng định dạng", error="Unauthorized")

        token = bearer_token.split(" ")[1]
        try:
            jwks = await self.get_certs()
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            key = None
            for k in jwks.get("keys", []):
                if k.get("kid") == kid:
                    key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(k))
                    break

            if not key:
                raise AppException(status_code=401, message="SSO Signing Key không hợp lệ", error="Unauthorized")

            payload = jwt.decode(token, key=key, algorithms=["RS256"], options={"verify_aud": False})
            return payload
        except jwt.PyJWTError as exc:
            logger.warn("SSO Token verification failed", error=str(exc))
            raise AppException(status_code=401, message="SSO Token không hợp lệ hoặc đã hết hạn", error="Unauthorized")

    async def init_user(self, payload: Dict[str, Any]) -> User:
        """Find or auto-create User on first SSO login."""
        sso_id = payload.get("sub")
        username = payload.get("preferred_username") or payload.get("username") or sso_id
        email = payload.get("email")
        firstname = payload.get("given_name") or payload.get("firstName")
        lastname = payload.get("family_name") or payload.get("lastName")
        fullname = f"{lastname or ''} {firstname or ''}".strip() or username

        stmt = select(User).where((User.sso_id == sso_id) | (User.username == username))
        res = await self.db.execute(stmt)
        user = res.scalar_one_or_none()

        if not user:
            user = User(
                sso_id=sso_id,
                username=username,
                email=email,
                firstname=firstname,
                lastname=lastname,
                full_name=fullname,
                system_role="USER",
            )
            self.db.add(user)
            await self.db.flush()
            await self.db.refresh(user)

        return user
