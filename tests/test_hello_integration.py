"""Integration check for the standalone hello HTTP service."""

from __future__ import annotations

import pytest
from aiohttp.test_utils import TestClient, TestServer

from octop_gateway.hello import create_app


@pytest.mark.integration
async def test_hello_service_responds_over_loopback() -> None:
    """The service answers GET /hello over a real loopback HTTP connection."""
    async with TestClient(TestServer(create_app())) as client:
        response = await client.get("/hello")
        assert response.status == 200
        assert await response.json() == {"message": "hello world"}
