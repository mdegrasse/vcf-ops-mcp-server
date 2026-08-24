import time

import httpx
import pytest
import respx

from vcf_ops_mcp.client import VCFOpsAPIError, VCFOpsAuthError, VCFOpsClient
from vcf_ops_mcp.config import Settings


def make_settings(**overrides) -> Settings:
    defaults = dict(
        base_url="https://ops.example.com",
        username="admin",
        password="secret",
        auth_source="LOCAL",
        verify_ssl=True,
        timeout=5.0,
    )
    defaults.update(overrides)
    return Settings(**defaults)


@pytest.mark.asyncio
@respx.mock
async def test_acquires_token_and_calls_api():
    respx.post("https://ops.example.com/suite-api/api/auth/token/acquire").mock(
        return_value=httpx.Response(200, json={"token": "tok-1", "validity": (time.time() + 1800) * 1000})
    )
    route = respx.get("https://ops.example.com/suite-api/api/resources").mock(
        return_value=httpx.Response(200, json={"resourceList": [{"identifier": "r1"}]})
    )

    client = VCFOpsClient(make_settings())
    try:
        data = await client.get("/resources")
    finally:
        respx.post("https://ops.example.com/suite-api/api/auth/token/release").mock(
            return_value=httpx.Response(204)
        )
        await client.aclose()

    assert data["resourceList"][0]["identifier"] == "r1"
    assert route.calls.last.request.headers["Authorization"] == "OpsToken tok-1"


@pytest.mark.asyncio
@respx.mock
async def test_retries_once_on_401_with_fresh_token():
    respx.post("https://ops.example.com/suite-api/api/auth/token/acquire").mock(
        side_effect=[
            httpx.Response(200, json={"token": "stale", "validity": (time.time() + 1800) * 1000}),
            httpx.Response(200, json={"token": "fresh", "validity": (time.time() + 1800) * 1000}),
        ]
    )
    respx.post("https://ops.example.com/suite-api/api/auth/token/release").mock(return_value=httpx.Response(204))

    calls = []

    def responder(request: httpx.Request) -> httpx.Response:
        calls.append(request.headers["Authorization"])
        if request.headers["Authorization"] == "OpsToken stale":
            return httpx.Response(401, json={"message": "expired"})
        return httpx.Response(200, json={"resourceList": []})

    respx.get("https://ops.example.com/suite-api/api/resources").mock(side_effect=responder)

    client = VCFOpsClient(make_settings())
    try:
        data = await client.get("/resources")
    finally:
        await client.aclose()

    assert data == {"resourceList": []}
    assert calls == ["OpsToken stale", "OpsToken fresh"]


@pytest.mark.asyncio
@respx.mock
async def test_auth_failure_raises():
    respx.post("https://ops.example.com/suite-api/api/auth/token/acquire").mock(
        return_value=httpx.Response(401, text="bad credentials")
    )

    client = VCFOpsClient(make_settings())
    with pytest.raises(VCFOpsAuthError):
        await client.get("/resources")
    await client._http.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_api_error_raises_with_status_code():
    respx.post("https://ops.example.com/suite-api/api/auth/token/acquire").mock(
        return_value=httpx.Response(200, json={"token": "tok-1", "validity": (time.time() + 1800) * 1000})
    )
    respx.get("https://ops.example.com/suite-api/api/resources/missing").mock(
        return_value=httpx.Response(404, json={"message": "not found"})
    )
    respx.post("https://ops.example.com/suite-api/api/auth/token/release").mock(return_value=httpx.Response(204))

    client = VCFOpsClient(make_settings())
    try:
        with pytest.raises(VCFOpsAPIError) as excinfo:
            await client.get("/resources/missing")
        assert excinfo.value.status_code == 404
    finally:
        await client.aclose()
