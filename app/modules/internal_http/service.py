"""
Internal HTTP Service — Port 1-1 từ internal-http.service.ts + internal-auth-http.service.ts.
Dùng httpx thay cho axios. Hỗ trợ API key auth và OAuth2 client credentials.
"""
import re
import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote as url_encode, urljoin

import httpx

from app.common.exceptions import AppException
from app.core.config import settings
from app.core.logging import logger


# ─── Constants port từ internal-http/common/constant.ts ─────────

INTERNAL_HTTP_CLIENTS = ["core", "file"]


def get_internal_http_client_config(client: str) -> Dict[str, str]:
    """Port 1-1 từ getInternalHttpClientConfig."""
    config_map = {
        "core": {
            "address": getattr(settings, "INTERNAL_HTTP_CORE_ADDRESS", ""),
            "apiKey": getattr(settings, "INTERNAL_HTTP_CORE_API_KEY", ""),
        },
        "file": {
            "address": getattr(settings, "INTERNAL_HTTP_FILE_ADDRESS", ""),
            "apiKey": getattr(settings, "INTERNAL_HTTP_FILE_API_KEY", ""),
        },
    }
    return config_map.get(client, {})


def get_internal_http_client_address(client: str) -> str:
    """Port 1-1 từ getInternalHttpClientAddress."""
    config = get_internal_http_client_config(client)
    address = config.get("address", "")
    if not address:
        raise AppException(
            status_code=500,
            message=f"Missing internal HTTP address for {client}",
            error="Internal Server Error",
        )
    return address


def normalize_endpoint(endpoint: str) -> List[str]:
    """Port 1-1 từ normalizeEndpoint."""
    ep = (endpoint or "").strip()
    if not ep or re.match(r'^(?:/|\\|//|[a-z][a-z0-9+.-]*:)', ep, re.IGNORECASE):
        raise AppException(status_code=400, message="Invalid internal HTTP endpoint", error="Bad Request")

    segments = ep.split("/")
    for seg in segments:
        if not seg or re.match(r'^(?:\.\.?)$', seg) or re.search(r'%2[ef]|%5c', seg, re.IGNORECASE):
            raise AppException(status_code=400, message="Invalid internal HTTP endpoint", error="Bad Request")
    return segments


def build_request_url(address: str, client: str, endpoint: str) -> str:
    """Port 1-1 từ buildRequestUrl."""
    from urllib.parse import urlparse, urlunparse
    parsed = urlparse(address)
    if parsed.scheme not in ("http", "https"):
        raise AppException(
            status_code=500,
            message=f"Unsupported internal HTTP protocol for {client}",
            error="Internal Server Error",
        )
    segments = normalize_endpoint(endpoint)
    base_path = parsed.path.rstrip("/")
    new_path = f"{base_path}/{'/'.join(url_encode(seg, safe='') for seg in segments)}"
    return urlunparse((parsed.scheme, parsed.netloc, new_path, "", "", ""))


def get_internal_http_request_url(client: str, endpoint: str) -> str:
    """Port 1-1 từ getInternalHttpRequestUrl."""
    address = get_internal_http_client_address(client)
    return build_request_url(address, client, endpoint)


class InternalHttpService:
    """Port 1-1 từ InternalHttpService (internal-http.service.ts:L16-70)."""

    def _get_http_client_api_key(self, client: str) -> str:
        """Port 1-1 từ private getHttpClientApiKey."""
        config = get_internal_http_client_config(client)
        return config.get("apiKey") or getattr(settings, "GW_API_KEY", "")

    async def request(
        self,
        client: str,
        method: str,
        endpoint: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """Port 1-1 từ request(client, method, endpoint, options)."""
        options = options or {}
        api_key = self._get_http_client_api_key(client)
        url = get_internal_http_request_url(client, endpoint)

        headers = dict(options.get("header", {}))
        headers["x-gw-api-key"] = api_key

        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.request(
                method=method.upper(),
                url=url,
                json=options.get("data"),
                params=options.get("params"),
                headers=headers,
            )
            return response


class InternalAuthHttpService:
    """Port 1-1 từ InternalAuthHttpService (internal-auth-http.service.ts:L21-163).
    Dùng OAuth2 client_credentials flow thay vì API key."""

    def __init__(self):
        self._cached_access_token = ""
        self._cached_token_expire_at = 0

    async def _get_access_token(self) -> str:
        """Port 1-1 từ getAccessToken + requestAccessToken."""
        now = time.time() * 1000  # milliseconds
        if self._cached_access_token and (now + 5000) < self._cached_token_expire_at:
            return self._cached_access_token

        return await self._request_access_token()

    async def _request_access_token(self) -> str:
        """Port 1-1 từ requestAccessToken."""
        token_url = getattr(settings, "OAUTH2_TOKEN_URL", "")
        client_id = getattr(settings, "OAUTH2_CLIENT_ID", "")
        client_secret = getattr(settings, "OAUTH2_CLIENT_SECRET", "")

        if not token_url or not client_id or not client_secret:
            raise AppException(
                status_code=500,
                message="Missing OAuth2 client credential configuration",
                error="Internal Server Error",
            )

        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }
        scope = getattr(settings, "OAUTH2_SCOPE", None)
        if scope:
            data["scope"] = scope
        audience = getattr(settings, "OAUTH2_AUDIENCE", None)
        if audience:
            data["audience"] = audience

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                token_url,
                data=data,
                headers={"content-type": "application/x-www-form-urlencoded"},
            )
            resp_data = response.json()

        if not resp_data.get("access_token"):
            raise AppException(
                status_code=500,
                message="OAuth2 response does not contain access_token",
                error="Internal Server Error",
            )

        expires_in = int(resp_data.get("expires_in", 60))
        self._cached_access_token = resp_data["access_token"]
        self._cached_token_expire_at = time.time() * 1000 + max(expires_in, 1) * 1000

        return self._cached_access_token

    async def request(
        self,
        client: str,
        method: str,
        endpoint: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """Port 1-1 từ request(client, method, endpoint, options)."""
        options = options or {}
        access_token = await self._get_access_token()
        url = get_internal_http_request_url(client, endpoint)

        headers = dict(options.get("header", {}))
        headers["Authorization"] = f"Bearer {access_token}"

        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.request(
                method=method.upper(),
                url=url,
                json=options.get("data"),
                params=options.get("params"),
                headers=headers,
            )
            return response
