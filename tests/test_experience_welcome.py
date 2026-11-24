"""Contract tests for the native ``GET /welcome`` route."""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from urllib.error import HTTPError
from urllib.request import urlopen

import pytest

from octop_gateway.web import create_server


@pytest.fixture
def port() -> Iterator[int]:
    server = create_server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _get(port: int, path: str) -> tuple[int, str, bytes]:
    with urlopen(f"http://127.0.0.1:{port}{path}", timeout=5) as response:
        return response.status, response.headers.get("Content-Type", ""), response.read()


def test_welcome_returns_json(port: int) -> None:
    status, content_type, body = _get(port, "/welcome")
    assert status == 200
    assert content_type.startswith("application/json")
    assert json.loads(body) == {"message": "welcome"}


def test_welcome_needs_no_auth(port: int) -> None:
    status, _, body = _get(port, "/welcome")
    assert status == 200
    assert json.loads(body)["message"] == "welcome"


def test_unknown_path_returns_404(port: int) -> None:
    with pytest.raises(HTTPError) as error:
        _get(port, "/not-found")
    assert error.value.code == 404
