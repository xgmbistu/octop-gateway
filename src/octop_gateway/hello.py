"""Minimal standalone hello HTTP service."""

from __future__ import annotations

from aiohttp import web

HOST = "127.0.0.1"
PORT = 8080
HELLO_MESSAGE = "hello world"


async def hello(_request: web.Request) -> web.Response:
    """Return the fixed hello payload as JSON."""
    return web.json_response({"message": HELLO_MESSAGE})


def create_app() -> web.Application:
    """Build an application exposing ``GET /hello``."""
    app = web.Application()
    app.router.add_get("/hello", hello)
    return app


def main() -> None:
    """Run the service on the local loopback interface."""
    web.run_app(create_app(), host=HOST, port=PORT)


if __name__ == "__main__":
    main()
