"""The outbound HTTP contract (constitution v1.36.0, MCP Server profile Layer 3).

Every test here drives a real `httpx.AsyncClient` over a `MockTransport`. That
is the point: the agent string is set by the client and the ceiling is enforced
while the client reads, so an `AsyncMock` standing in for the client would mock
away the behaviour under test.
"""

from collections.abc import AsyncIterator
from importlib.metadata import version

import httpx
import pytest

from mcp_mediawiki_crunchtools import client as client_mod
from mcp_mediawiki_crunchtools.errors import MediaWikiApiError
from tests.conftest import _transport


async def _endless(chunk: bytes, times: int) -> AsyncIterator[bytes]:
    """A chunked body, which carries no content-length -- the case a header check misses."""
    for _ in range(times):
        yield chunk


def _client() -> client_mod.MediaWikiClient:
    return client_mod.MediaWikiClient()


class TestUserAgent:
    """A request says what it is, and the version cannot drift from the release."""

    @pytest.mark.asyncio
    async def test_outgoing_request_names_the_product_and_version(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MEDIAWIKI_URL", "https://example.com/w")
        seen: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request.headers["User-Agent"])
            return httpx.Response(200, json={"query": {}})

        with _transport(handler):
            await _client()._request("GET", params={"action": "query", "format": "json"})

        expected = (
            f"mcp-mediawiki-crunchtools/{version('mcp-mediawiki-crunchtools')} "
            "(+https://github.com/crunchtools/mcp-mediawiki)"
        )
        assert seen == [expected]
        assert "python-httpx" not in seen[0]


class TestResponseCeiling:
    """The cap is enforced while reading, not taken from a header."""

    @pytest.mark.asyncio
    async def test_chunked_body_over_the_cap_is_rejected(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No content-length at all: this is what a header check lets through."""
        monkeypatch.setenv("MEDIAWIKI_URL", "https://example.com/w")
        monkeypatch.setattr(client_mod, "MAX_RESPONSE_SIZE", 4096)

        def handler(_request: httpx.Request) -> httpx.Response:
            response = httpx.Response(
                200,
                headers={"content-type": "application/json"},
                content=_endless(b"x" * 1024, 16),
            )
            assert "content-length" not in response.headers
            return response

        with _transport(handler), pytest.raises(MediaWikiApiError) as caught:
            await _client()._request("GET", params={"action": "query"})

        message = str(caught.value)
        assert "4096" in message
        assert "https://example.com/w/api.php" in message
        assert "GET" in message

    @pytest.mark.asyncio
    async def test_declared_length_over_the_cap_is_rejected_early(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MEDIAWIKI_URL", "https://example.com/w")
        monkeypatch.setattr(client_mod, "MAX_RESPONSE_SIZE", 64)

        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200, headers={"content-type": "application/json"}, content=b"x" * 128
            )

        with _transport(handler), pytest.raises(MediaWikiApiError) as caught:
            await _client()._request("GET", params={"action": "query"})

        assert "declared 128 bytes" in str(caught.value)

    @pytest.mark.asyncio
    async def test_a_malformed_content_length_does_not_crash(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`int()` on an unchecked header is a ValueError escaping as itself."""
        monkeypatch.setenv("MEDIAWIKI_URL", "https://example.com/w")

        def handler(_request: httpx.Request) -> httpx.Response:
            response = httpx.Response(200, json={"query": {}})
            response.headers["content-length"] = "not-a-number"
            return response

        with _transport(handler):
            result = await _client()._request("GET", params={"action": "query"})

        assert result == {"query": {}}


class TestErrorNamesTheSite:
    """RT #1596: the message has to say which site answered, and with what."""

    @pytest.mark.asyncio
    async def test_non_json_body_names_url_status_type_and_a_snippet(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MEDIAWIKI_URL", "https://example.com/w")
        challenge = "<!DOCTYPE html><title>Just a moment...</title>"

        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200, headers={"content-type": "text/html; charset=UTF-8"}, text=challenge
            )

        with _transport(handler), pytest.raises(MediaWikiApiError) as caught:
            await _client()._request("GET", params={"action": "query"})

        message = str(caught.value)
        assert "GET" in message
        assert "https://example.com/w/api.php?action=query" in message
        assert "text/html" in message
        assert "Just a moment" in message

    @pytest.mark.asyncio
    async def test_error_status_names_the_site_and_the_body(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MEDIAWIKI_URL", "https://example.com/w")

        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                403, headers={"content-type": "text/html"}, text="Attention Required!"
            )

        with _transport(handler), pytest.raises(MediaWikiApiError) as caught:
            await _client()._request("GET", params={"action": "query"})

        message = str(caught.value)
        assert "HTTP 403" in message
        assert "example.com" in message
        assert "Attention Required!" in message

    @pytest.mark.asyncio
    async def test_an_empty_body_says_so_rather_than_nothing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MEDIAWIKI_URL", "https://example.com/w")

        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(502, headers={"content-type": "text/plain"}, content=b"")

        with _transport(handler), pytest.raises(MediaWikiApiError) as caught:
            await _client()._request("GET", params={"action": "query"})

        assert "<empty body>" in str(caught.value)


class TestErrorRedaction:
    """Layer 1 applies to an error message: the URL in it carries no secret."""

    @pytest.mark.asyncio
    async def test_userinfo_and_credential_params_are_redacted(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A configured `https://bot:password@host/w/` is supported, and secret."""
        monkeypatch.setenv("MEDIAWIKI_URL", "https://bot:sekrit@example.com/w")

        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(403, headers={"content-type": "text/html"}, text="denied")

        with _transport(handler), pytest.raises(MediaWikiApiError) as caught:
            await _client()._request("GET", params={"action": "query", "token": "csrf-secret"})

        message = str(caught.value)
        assert "sekrit" not in message
        assert "csrf-secret" not in message
        # What is left is still the diagnosis: which host, and which action.
        assert "example.com/w/api.php" in message
        assert "action=query" in message
