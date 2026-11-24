"""Contract tests for the optional standalone hello HTTP service."""

from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from octop_gateway.hello import create_app


async def test_hello_returns_json() -> None:
    """GET /hello returns 200 with the documented JSON payload."""
    async with TestClient(TestServer(create_app())) as client:
        response = await client.get("/hello")
        assert response.status == 200
        assert "application/json" in response.headers["Content-Type"]
        assert await response.json() == {"message": "hello world"}


async def test_unknown_path_returns_404() -> None:
    """Unregistered paths are rejected by the router."""
    async with TestClient(TestServer(create_app())) as client:
        response = await client.get("/not-found")

    assert response.status == 404


async def test_non_get_method_returns_405() -> None:
    """The hello resource only accepts GET (and implicit HEAD)."""
    async with TestClient(TestServer(create_app())) as client:
        response = await client.post("/hello")

    assert response.status == 405


def test_create_app_registers_get_route() -> None:
    """create_app exposes an aiohttp application with GET /hello."""
    app = create_app()

    assert isinstance(app, web.Application)
    assert any(
        getattr(route.resource, "canonical", None) == "/hello" and route.method == "GET"
        for route in app.router.routes()
    )


def test_main_binds_local_loopback(monkeypatch: pytest.MonkeyPatch) -> None:
    """main starts the app on the documented local host and port."""
    from octop_gateway import hello

    captured: dict[str, object] = {}

    def fake_run_app(app: web.Application, *, host: str, port: int) -> None:
        captured["app"] = app
        captured["host"] = host
        captured["port"] = port

    monkeypatch.setattr(hello.web, "run_app", fake_run_app)
    hello.main()

    assert captured["host"] == "127.0.0.1"
    assert captured["port"] == 8080
    assert isinstance(captured["app"], web.Application)
