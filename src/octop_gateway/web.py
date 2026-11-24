"""Minimal native HTTP service exposing the ``GET /welcome`` route.

Run with ``python -m octop_gateway.web``. Host and port are configurable via
``WALLY_HOST`` / ``WALLY_PORT`` (defaults: ``0.0.0.0`` / ``8080``).
"""

from __future__ import annotations

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

WELCOME_PATH = "/welcome"
_WELCOME_BODY = json.dumps({"message": "welcome"}).encode("utf-8")


class WelcomeHandler(BaseHTTPRequestHandler):
    """Handle native HTTP requests; only ``GET /welcome`` is served."""

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        path = self.path.split("?", 1)[0]
        if path == WELCOME_PATH:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(_WELCOME_BODY)))
            self.end_headers()
            self.wfile.write(_WELCOME_BODY)
        else:
            self.send_error(404)

    def log_message(self, fmt: str, *args: object) -> None:
        """Suppress per-request stderr logging."""


def create_server(host: str = "0.0.0.0", port: int = 8080) -> ThreadingHTTPServer:
    """Build a :class:`ThreadingHTTPServer` bound to ``host:port``."""
    return ThreadingHTTPServer((host, port), WelcomeHandler)


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the native GET /welcome endpoint.")
    parser.add_argument("--host", default=os.environ.get("WALLY_HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("WALLY_PORT", "8080")))
    args = parser.parse_args()
    server = create_server(args.host, args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
