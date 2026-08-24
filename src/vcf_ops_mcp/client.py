from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx

from .config import Settings

API_PREFIX = "/suite-api/api"

# Refresh the token this many seconds before it actually expires, to avoid
# racing a request against expiry.
TOKEN_REFRESH_SKEW_SECONDS = 60


class VCFOpsAuthError(RuntimeError):
    pass


class VCFOpsAPIError(RuntimeError):
    def __init__(self, status_code: int, message: str, body: Any = None):
        super().__init__(f"VCF Operations API error {status_code}: {message}")
        self.status_code = status_code
        self.body = body


class VCFOpsClient:
    """Async client for the VCF Operations (vROps) suite-api REST API.

    Handles token-based authentication (acquire/refresh/release) so tool
    implementations can just call the resource/stats/alerts methods below.
    """

    def __init__(self, settings: Settings):
        self._settings = settings
        self._http = httpx.AsyncClient(
            base_url=settings.base_url.rstrip("/"),
            verify=settings.verify_ssl,
            timeout=settings.timeout,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )
        self._token: str | None = None
        self._token_expires_at: float = 0.0
        self._auth_lock = asyncio.Lock()

    async def aclose(self) -> None:
        try:
            if self._token:
                await self._release_token()
        finally:
            await self._http.aclose()

    async def __aenter__(self) -> "VCFOpsClient":
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()

    # -- authentication -----------------------------------------------

    async def _acquire_token(self) -> None:
        response = await self._http.post(
            f"{API_PREFIX}/auth/token/acquire",
            json={
                "username": self._settings.username,
                "password": self._settings.password,
                "authSource": self._settings.auth_source,
            },
        )
        if response.status_code != 200:
            raise VCFOpsAuthError(
                f"Failed to acquire VCF Operations auth token "
                f"(HTTP {response.status_code}): {response.text}"
            )
        data = response.json()
        token = data.get("token")
        if not token:
            raise VCFOpsAuthError("Auth response did not include a token")
        self._token = token
        validity_ms = data.get("validity")
        if isinstance(validity_ms, (int, float)):
            self._token_expires_at = validity_ms / 1000.0
        else:
            # Fall back to a conservative 30 minute lifetime if the server
            # doesn't report an expiry.
            self._token_expires_at = time.time() + 1800

    async def _release_token(self) -> None:
        token, self._token = self._token, None
        if not token:
            return
        try:
            await self._http.post(
                f"{API_PREFIX}/auth/token/release",
                headers={"Authorization": f"OpsToken {token}"},
            )
        except httpx.HTTPError:
            pass

    async def _ensure_token(self) -> str:
        async with self._auth_lock:
            if not self._token or time.time() >= self._token_expires_at - TOKEN_REFRESH_SKEW_SECONDS:
                await self._acquire_token()
        assert self._token is not None
        return self._token

    # -- request plumbing -----------------------------------------------

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
    ) -> Any:
        token = await self._ensure_token()
        response = await self._http.request(
            method,
            f"{API_PREFIX}{path}",
            params=_clean_params(params),
            json=json,
            headers={"Authorization": f"OpsToken {token}"},
        )

        if response.status_code == 401:
            # Token may have been invalidated server-side; force one refresh and retry.
            async with self._auth_lock:
                self._token = None
            token = await self._ensure_token()
            response = await self._http.request(
                method,
                f"{API_PREFIX}{path}",
                params=_clean_params(params),
                json=json,
                headers={"Authorization": f"OpsToken {token}"},
            )

        if response.status_code == 204:
            return None
        if not response.is_success:
            try:
                body = response.json()
                message = body.get("message", response.text)
            except ValueError:
                body = response.text
                message = response.text
            raise VCFOpsAPIError(response.status_code, message, body)

        if not response.content:
            return None
        return response.json()

    async def get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return await self.request("GET", path, params=params)

    async def post(self, path: str, *, params: dict[str, Any] | None = None, json: Any = None) -> Any:
        return await self.request("POST", path, params=params, json=json)


def _clean_params(params: dict[str, Any] | None) -> dict[str, Any] | None:
    """Drop None values and normalize bools so httpx encodes them the way the API expects."""
    if not params:
        return None
    cleaned: dict[str, Any] = {}
    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, bool):
            cleaned[key] = str(value).lower()
        else:
            cleaned[key] = value
    return cleaned or None
