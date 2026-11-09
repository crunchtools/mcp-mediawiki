"""Shared test fixtures for mcp-mediawiki tests."""

import os
from collections.abc import Callable, Generator, Iterable
from typing import Any
from unittest.mock import patch

import httpx
import pytest


@pytest.fixture(autouse=True)
def _reset_client_singleton() -> Generator[None, None, None]:
    """Reset the global client and config singletons between tests."""
    import mcp_mediawiki_crunchtools.client as client_mod
    import mcp_mediawiki_crunchtools.config as config_mod

    client_mod._client = None
    config_mod._config = None
    yield
    client_mod._client = None
    config_mod._config = None


def _mock_response(
    status_code: int = 200,
    json_data: dict | list | None = None,
    text: str = "",
    content_type: str = "application/json",
    headers: dict | None = None,
) -> httpx.Response:
    """Build a mock httpx.Response."""
    resp_headers = {"content-type": content_type}
    if headers:
        resp_headers.update(headers)
    return httpx.Response(
        status_code=status_code,
        headers=resp_headers,
        json=json_data if json_data is not None else None,
        text=text if json_data is None else None,
        request=httpx.Request("GET", "https://example.com/w/api.php"),
    )


Handler = Callable[[httpx.Request], httpx.Response]


def _answer(template: httpx.Response, request: httpx.Request) -> httpx.Response:
    """A fresh response with a template's status, type and body, for one request.

    Fresh because a streamed body can be read once, and because the error
    messages under test name `response.request.url` -- which is the URL the
    client actually built, not the placeholder a template carries. Content-length
    is dropped so httpx recomputes it for the body it is given.
    """
    headers = {k: v for k, v in template.headers.items() if k.lower() != "content-length"}
    return httpx.Response(
        template.status_code, headers=headers, content=template.content, request=request
    )


def _transport(handler: Handler):
    """Put every client the process builds on a MockTransport running `handler`.

    A real `httpx.AsyncClient` over a fake transport, rather than an AsyncMock
    standing in for the client: the client is what reads the body in bounded
    pieces and sets the User-Agent, so mocking its methods would mock away the
    behaviour these tests exist to hold (constitution 1.36.0, Layer 3).
    """
    real = httpx.AsyncClient

    def factory(**kwargs: Any) -> httpx.AsyncClient:
        kwargs.pop("transport", None)
        return real(transport=httpx.MockTransport(handler), **kwargs)

    return patch.object(httpx, "AsyncClient", factory)


def _patch_client(mock_response: httpx.Response):
    """Serve one response to every request, over a real client and a fake transport.

    Sets MEDIAWIKI_URL so config initializes.
    """
    import mcp_mediawiki_crunchtools.client as client_mod
    import mcp_mediawiki_crunchtools.config as config_mod

    client_mod._client = None
    config_mod._config = None

    os.environ.setdefault("MEDIAWIKI_URL", "https://example.com/w")

    return _transport(lambda request: _answer(mock_response, request))


def _patch_client_sequence(responses: Iterable[httpx.Response]):
    """Serve an ordered sequence, for a flow that makes several calls.

    One request too many is an assertion rather than a silent repeat, so a
    login flow that grows a call fails loudly.
    """
    import mcp_mediawiki_crunchtools.client as client_mod
    import mcp_mediawiki_crunchtools.config as config_mod

    client_mod._client = None
    config_mod._config = None

    os.environ.setdefault("MEDIAWIKI_URL", "https://example.com/w")
    remaining = iter(list(responses))

    def handler(request: httpx.Request) -> httpx.Response:
        try:
            return _answer(next(remaining), request)
        except StopIteration:
            raise AssertionError(f"unexpected request: {request.method} {request.url}") from None

    return _transport(handler)
