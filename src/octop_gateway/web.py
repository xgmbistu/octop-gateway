"""Minimal aiohttp web service exposing the native ``GET /welcome`` route.

This module provides a standalone entrypoint so the route can be served and
contract-tested without depending on any IM channel runtime.
"""

from __future__ import annotations

import argparse

from aiohttp import web


async def _welcome(request: web.Request) -> web.Response:
    """Return the welcome payload without requiring authentication."""
    return web.json_response({"message": "welcome"})


def create_app() -> web.Application:
    """Build the aiohttp application with the native ``GET /welcome`` route."""
    app = web.Application()
    app.router.add_get("/welcome", _welcome)
    return app


def run_app() -> None:
    """Run the web service (host/port overridable via CLI arguments)."""
    parser = argparse.ArgumentParser(description="octop-gateway welcome web service")
    parser.add_argument("--host", default="0.0.0.0", help="bind address (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8080, help="bind port (default: 8080)")
    args = parser.parse_args()
    web.run_app(create_app(), host=args.host, port=args.port)


if __name__ == "__main__":
    run_app()
