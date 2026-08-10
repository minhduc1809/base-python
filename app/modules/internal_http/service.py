"""
Internal HTTP Service.
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


INTERNAL_HTTP_CLIENTS = ["core", "file"]


def get_internal_http_client_config(client: str) -> Dict[str, str]:
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
    config = get_internal_http_client_config(client)
    address = config.get("address", "")
    if not address:
        raise AppException(
            status_code=500,
            message=f"Missing internal HTTP address for {client}",
            error="Internal Server Error",
        )
    return address


def normalize_endpoint(endpoint: str) -> str:
    if not endpoint:
        return ""
    prefix = "" if endpoint.startswith("/") else "/"
    return f"{prefix}{endpoint}"


def build_request_url(address: str, client: str, endpoint: str) -> str:
    cleaned_endpoint = normalize_endpoint(endpoint)

    if address.endswith("/"):
        base_address = address[:-1]
    else:
        base_address = address

    # Format params / parameters
    pattern = r"//+"
    raw_url = f"{base_address}{cleaned_endpoint}"
    # Normalize multiple slashes except http:// or https://
    proto_match = re.match(r"^(https?://)", raw_url)
    if proto_match:
        protocol = proto_match.group(1)
        path = raw_url[len(protocol) :]
        path = re.sub(pattern, "/", path)
        return f"{protocol}{path}"
    return re.sub(pattern, "/", raw_url)


def get_internal_http_request_url(client: str, endpoint: str) -> str:
    address = get_internal_http_client_address(client)
    return build_request_url(address, client, endpoint)


class InternalHttpService:
    def _get_http_client_api_key(self, client: str) -> str:
        config = get_internal_http_client_config(client)
        return config.get("apiKey") or getattr(settings, "GW_API_KEY", "")

    async def request(
        self,
        client: str,
        method: str,
        endpoint: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
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
    """Service HTTP nội bộ sử dụng OAuth2 client_credentials flow."""

    def __init__(self):
        self._cached_access_token = ""
        self._cached_token_expire_at = 0

    async def _get_access_token(self) -> str:
        now = time.time() * 1000  # milliseconds
        if self._cached_access_token and (now + 5000) < self._cached_token_expire_at:
            return self._cached_access_token

        return await self._request_access_token()

    async def _request_access_token(self) -> str:
        token_url = getattr(settings, "OAUTH2_TOKEN_URL", "")
        client_id = getattr(settings, "OAUTH2_CLIENT_ID", "")
        client_secret = getattr(settings, "OAUTH2_CLIENT_SECRET", "")

        if not token_url:
            return "mock-access-token"

        payload = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(token_url, data=payload)
            if resp.status_code != 200:
                raise AppException(
                    status_code=resp.status_code,
                    message="Failed to request OAuth2 access token",
                    error="Unauthorized",
                )
            data = resp.json()
            token = data.get("access_token", "")
            expires_in = data.get("expires_in", 3600)  # seconds
            self._cached_access_token = token
            self._cached_token_expire_at = (time.time() + expires_in) * 1000
            return token

    async def request(
        self,
        client: str,
        method: str,
        endpoint: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        options = options or {}
        token = await self._get_access_token()
        url = get_internal_http_request_url(client, endpoint)

        headers = dict(options.get("header", {}))
        headers["Authorization"] = f"Bearer {token}"

        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.request(
                method=method.upper(),
                url=url,
                json=options.get("data"),
                params=options.get("params"),
                headers=headers,
            )
            return response
