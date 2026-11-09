"""MediaWiki Action API client with security hardening.

This module provides a secure async HTTP client for the MediaWiki Action API.
All requests go through this client to ensure consistent security practices.

Authentication flow for write operations:
1. action=query&meta=tokens&type=login -> get login token
2. action=clientlogin with username, password, login token
3. Session cookies stored in persistent httpx client
4. Before each write: action=query&meta=tokens&type=csrf -> CSRF token
5. CSRF token included in edit/delete/move requests
"""

import json
import logging
from importlib.metadata import version
from typing import Any

import httpx

from .config import get_config
from .errors import (
    AuthenticationError,
    MediaWikiApiError,
    PageNotFoundError,
    PermissionDeniedError,
    RateLimitError,
)

logger = logging.getLogger(__name__)

MAX_RESPONSE_SIZE = 10 * 1024 * 1024
REQUEST_TIMEOUT = 30.0

# Identify this client by name. httpx otherwise sends `python-httpx/<version>`,
# which Wikimedia's User-Agent policy refuses outright and which Cloudflare's
# bot protection answers with an HTML challenge page instead of the API -- the
# failure that cost an afternoon on mcp-wordpress (RT #1596). The version comes
# from installed package metadata rather than `from . import __version__`,
# because this package's `__init__` imports the server and that import would
# close a cycle.
USER_AGENT = (
    f"mcp-mediawiki-crunchtools/{version('mcp-mediawiki-crunchtools')} "
    "(+https://github.com/crunchtools/mcp-mediawiki)"
)

# How much of a body to quote back in an error. Enough to recognise a WAF page,
# a login redirect or a proxy error; short enough to stay readable.
BODY_SNIPPET_CHARS = 200


def _body_snippet(body: bytes) -> str:
    """A short, single-line excerpt of a response body, for an error message."""
    # Slice the bytes, then decode only that: a WAF page can be megabytes, and
    # decoding all of it to keep 200 characters copies it twice for nothing.
    # Four times the snippet is enough slack for the whitespace a collapse
    # removes; `replace` covers a multi-byte character the slice cut in half.
    prefix = body[: BODY_SNIPPET_CHARS * 4]
    collapsed = " ".join(prefix.decode("utf-8", errors="replace").split())
    if not collapsed:
        return "<empty body>"
    if len(collapsed) > BODY_SNIPPET_CHARS or len(body) > len(prefix):
        return collapsed[:BODY_SNIPPET_CHARS] + "..."
    return collapsed


def _where(response: httpx.Response) -> str:
    """Which request a response answered, for an error message.

    `request.url` and not the configured api_url: an `http` base that 301s to
    `https` returns an HTML body and reproduces this module's JSON error byte
    for byte, and only the URL actually requested tells the two apart.
    """
    return (
        f"{response.request.method} {response.request.url} "
        f"(HTTP {response.status_code}, {response.headers.get('content-type', 'no content-type')})"
    )


async def _read_capped(response: httpx.Response) -> bytes:
    """Read the body, aborting as soon as it passes MAX_RESPONSE_SIZE.

    The cap is enforced while reading. A `content-length` check alone is not a
    ceiling: the header is optional, so a chunked reply carries none and walks
    straight past it.
    """
    declared = response.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > MAX_RESPONSE_SIZE:
        raise MediaWikiApiError(
            "oversize",
            f"{_where(response)} declared {declared} bytes, over the "
            f"{MAX_RESPONSE_SIZE} byte limit",
        )
    chunks: list[bytes] = []
    size = 0
    async for chunk in response.aiter_bytes():
        size += len(chunk)
        if size > MAX_RESPONSE_SIZE:
            raise MediaWikiApiError(
                "oversize",
                f"{_where(response)} sent over the {MAX_RESPONSE_SIZE} byte limit",
            )
        chunks.append(chunk)
    return b"".join(chunks)


class MediaWikiClient:
    """Async HTTP client for the MediaWiki Action API.

    Security features:
    - Configurable base URL with HTTPS enforcement
    - Credentials passed via POST body (not URL)
    - TLS certificate validation (httpx default)
    - Request timeout enforcement
    - Response size limits
    - MediaWiki continuation-based pagination
    - CSRF token management for write operations
    """

    def __init__(self) -> None:
        """Initialize the MediaWiki client."""
        self._config = get_config()
        self._client: httpx.AsyncClient | None = None
        self._csrf_token: str | None = None
        self._logged_in = False

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client with cookie persistence."""
        if self._client is None:
            auth = None
            if self._config.http_auth:
                user, passwd = self._config.http_auth
                auth = httpx.BasicAuth(user, passwd)

            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(REQUEST_TIMEOUT),
                auth=auth,
                headers={"User-Agent": USER_AGENT},
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            self._logged_in = False
            self._csrf_token = None

    async def _login(self) -> None:
        """Authenticate via action=login if credentials are configured.

        Uses the legacy action=login API which is exempted from read
        restrictions on private wikis (where action=query is blocked
        for anonymous users).

        Raises:
            AuthenticationError: If login fails.
        """
        if self._logged_in or not self._config.has_credentials:
            return

        token_data = await self._request(
            "POST",
            data={
                "action": "login",
                "lgname": self._config.username,
                "lgpassword": self._config.password,
                "format": "json",
            },
        )
        login_result = token_data.get("login", {})

        if login_result.get("result") == "NeedToken":
            login_token = login_result["token"]
        else:
            raise AuthenticationError(
                f"Unexpected login response: {login_result.get('result', 'unknown')}"
            )

        login_data = await self._request(
            "POST",
            data={
                "action": "login",
                "lgname": self._config.username,
                "lgpassword": self._config.password,
                "lgtoken": login_token,
                "format": "json",
            },
        )
        status = login_data.get("login", {}).get("result")

        if status != "Success":
            message = login_data.get("login", {}).get("reason", status or "Unknown error")
            raise AuthenticationError(f"Login failed: {message}")

        self._logged_in = True
        logger.info("Successfully authenticated as %s", self._config.username)

    async def _get_csrf_token(self) -> str:
        """Get a CSRF token for write operations.

        Returns:
            CSRF token string.
        """
        await self._login()

        token_response = await self._request(
            "GET",
            params={
                "action": "query",
                "meta": "tokens",
                "type": "csrf",
                "format": "json",
            },
        )
        self._csrf_token = token_response["query"]["tokens"]["csrftoken"]
        return self._csrf_token

    async def _request(
        self,
        method: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """The one way a request leaves this module.

        Every call site routed through here so the agent string, the ceiling and
        the error detail cannot be forgotten in one of them -- which is how
        `_login` ended up calling `.json()` on an unchecked body, where a
        challenge page surfaces as a bare JSONDecodeError.

        An `"error"` key in the payload is left for the caller: `post_action`
        has to see `badtoken` itself before the generic handler turns it into a
        user error.

        Raises:
            MediaWikiApiError: on a transport failure, an oversized body, an
                unsuccessful status, or a body that is not JSON.
        """
        client = await self._get_client()
        request = client.build_request(method, self._config.api_url, params=params, data=data)
        try:
            response = await client.send(request, stream=True)
            try:
                body = await _read_capped(response)
            finally:
                await response.aclose()
        except httpx.TimeoutException as e:
            raise MediaWikiApiError("timeout", f"Request timeout: {e}") from e
        except httpx.RequestError as e:
            raise MediaWikiApiError("network", f"Request failed: {e}") from e

        if not response.is_success:
            raise MediaWikiApiError(
                str(response.status_code),
                f"{_where(response)} returned {_body_snippet(body)}",
            )

        try:
            payload: dict[str, Any] = json.loads(body)
        except ValueError as e:
            raise MediaWikiApiError(
                "invalid_json",
                f"{_where(response)} is not JSON ({e}): {_body_snippet(body)}",
            ) from e
        return payload

    async def _fetch_query(self, all_params: dict[str, Any]) -> dict[str, Any]:
        """Execute a single query request and validate the response.

        Args:
            all_params: Complete query parameters including action and format.

        Returns:
            Parsed JSON response data.
        """
        response_json = await self._request("GET", params=all_params)

        if "error" in response_json:
            self._handle_api_error(response_json["error"])

        return response_json

    async def query(
        self,
        params: dict[str, Any],
        continue_key: str | None = None,
        max_pages: int = 1,
    ) -> dict[str, Any]:
        """Make a query action request with optional continuation.

        Args:
            params: Query parameters (action=query is added automatically).
            continue_key: Key for continuation (e.g., "sroffset" for search).
            max_pages: Maximum number of continuation pages to fetch.

        Returns:
            Combined query results.
        """
        await self._login()

        all_params = {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            **params,
        }

        query_result = await self._fetch_query(all_params)

        if max_pages <= 1 or "continue" not in query_result or not continue_key:
            return query_result

        return await self._fetch_continuation(all_params, query_result, max_pages)

    async def _fetch_continuation(
        self,
        all_params: dict[str, Any],
        initial_data: dict[str, Any],
        max_pages: int,
    ) -> dict[str, Any]:
        """Fetch additional pages of results via MediaWiki continuation.

        Args:
            all_params: Base query parameters.
            initial_data: First page response data (must contain "continue").
            max_pages: Maximum total pages to fetch.

        Returns:
            Combined query results from all pages.
        """
        combined: dict[str, Any] = dict(initial_data.get("query", {}))
        page_result = initial_data
        pages_fetched = 1

        while "continue" in page_result and pages_fetched < max_pages:
            next_params = {**all_params, **page_result["continue"]}
            try:
                page_result = await self._fetch_query(next_params)
            except (MediaWikiApiError, httpx.HTTPError):
                break

            page_query = page_result.get("query", {})
            for key, value in page_query.items():
                if isinstance(value, list) and key in combined:
                    combined[key].extend(value)
                else:
                    combined[key] = value

            pages_fetched += 1

        return {"query": combined}

    async def parse(self, params: dict[str, Any]) -> dict[str, Any]:
        """Make a parse action request.

        Args:
            params: Parse parameters (action=parse is added automatically).

        Returns:
            Parse result data.
        """
        await self._login()

        all_params = {
            "action": "parse",
            "format": "json",
            "formatversion": "2",
            **params,
        }

        response_json = await self._request("GET", params=all_params)

        if "error" in response_json:
            self._handle_api_error(response_json["error"])

        return response_json

    async def post_action(
        self,
        action: str,
        data: dict[str, Any],
        use_csrf: bool = True,
    ) -> dict[str, Any]:
        """Make a POST action request (edit, delete, move).

        Args:
            action: The API action (edit, delete, move).
            data: POST body data.
            use_csrf: Whether to include a CSRF token (default: True).

        Returns:
            Action result data.

        Raises:
            AuthenticationError: If not authenticated for write operations.
            PermissionDeniedError: If the user lacks permissions.
        """
        if not self._config.has_credentials:
            raise AuthenticationError(
                "Write operations require MEDIAWIKI_USERNAME and MEDIAWIKI_PASSWORD"
            )

        post_data = {
            "action": action,
            "format": "json",
            "formatversion": "2",
            **data,
        }

        if use_csrf:
            csrf_token = await self._get_csrf_token()
            post_data["token"] = csrf_token

        result = await self._request("POST", data=post_data)

        if "error" in result:
            error_code = result["error"].get("code", "unknown")
            if error_code == "badtoken":
                self._csrf_token = None
                csrf_token = await self._get_csrf_token()
                post_data["token"] = csrf_token
                result = await self._request("POST", data=post_data)
                if "error" in result:
                    self._handle_api_error(result["error"])
            else:
                self._handle_api_error(result["error"])

        return result

    def _handle_api_error(self, error: dict[str, Any]) -> None:
        """Handle error responses from the MediaWiki API.

        Args:
            error: The error dict from the API response.

        Raises:
            Various UserError subclasses based on error type.
        """
        code = error.get("code", "unknown")
        info = error.get("info", "Unknown error")

        if code in ("missingtitle", "nosuchpageid"):
            raise PageNotFoundError(info)
        if code in ("protectedpage", "cantdelete", "permissiondenied", "blocked"):
            raise PermissionDeniedError(info)
        if code == "ratelimited":
            raise RateLimitError()
        if code in ("assertuserfailed", "assertbotfailed"):
            self._logged_in = False
            self._csrf_token = None
            raise AuthenticationError("Session expired")

        raise MediaWikiApiError(code, info)


_client: MediaWikiClient | None = None


def get_client() -> MediaWikiClient:
    """Get the global MediaWiki client instance."""
    global _client
    if _client is None:
        _client = MediaWikiClient()
    return _client
