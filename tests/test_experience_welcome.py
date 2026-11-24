"""Contract tests for the native ``GET /welcome`` route.

Served by ``octop_gateway.web.create_app``. No external service is required.
Tests drive aiohttp's test client via ``asyncio.run`` so no async pytest
plugin is needed.
"""

from __future__ import annotations

import asyncio

from aiohttp.test_utils import TestClient, TestServer

from octop_gateway.web import create_app


async def _get_welcome() -> tuple[int, str, object]:
    """Perform GET /welcome with no authentication headers."""
    async with TestClient(TestServer(create_app())) as client:
        resp = await client.get("/welcome")  # deliberately no Authorization header
        return resp.status, resp.content_type, await resp.json()


async def _post_welcome() -> int:
    """Perform POST /welcome to confirm the route is GET-only."""
    async with TestClient(TestServer(create_app())) as client:
        resp = await client.post("/welcome")
        return resp.status


def test_welcome_returns_json_without_auth() -> None:
    """GET /welcome is open and returns HTTP 200 JSON with message=welcome."""
    status, content_type, payload = asyncio.run(_get_welcome())
    assert status == 200
    assert content_type == "application/json"
    assert payload == {"message": "welcome"}


def test_welcome_is_native_get_route() -> None:
    """POST /welcome is rejected (405), proving a native GET-only route."""
    assert asyncio.run(_post_welcome()) == 405
