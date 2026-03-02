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

import logging
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
        """Authenticate via clientlogin if credentials are configured.

        Raises:
            AuthenticationError: If login fails.
        """
        if self._logged_in or not self._config.has_credentials:
            return

        client = await self._get_client()

        token_resp = await client.get(
            self._config.api_url,
            params={
                "action": "query",
                "meta": "tokens",
                "type": "login",
                "format": "json",
            },
        )
        token_data = token_resp.json()
        login_token = token_data["query"]["tokens"]["logintoken"]

        login_resp = await client.post(
            self._config.api_url,
            data={
                "action": "clientlogin",
                "username": self._config.username,
                "password": self._config.password,
                "logintoken": login_token,
                "loginreturnurl": self._config.wiki_url,
                "format": "json",
            },
        )
        login_data = login_resp.json()

        status = login_data.get("clientlogin", {}).get("status")
        if status != "PASS":
            message = login_data.get("clientlogin", {}).get("message", "Unknown error")
            raise AuthenticationError(message)

        self._logged_in = True
        logger.info("Successfully authenticated as %s", self._config.username)

    async def _get_csrf_token(self) -> str:
        """Get a CSRF token for write operations.

        Returns:
            CSRF token string.
        """
        await self._login()
        client = await self._get_client()

        resp = await client.get(
            self._config.api_url,
            params={
                "action": "query",
                "meta": "tokens",
                "type": "csrf",
                "format": "json",
            },
        )
        data = resp.json()
        self._csrf_token = data["query"]["tokens"]["csrftoken"]
        return self._csrf_token

    async def _fetch_query(
        self, all_params: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a single query request and validate the response.

        Args:
            all_params: Complete query parameters including action and format.

        Returns:
            Parsed JSON response data.
        """
        client = await self._get_client()

        try:
            response = await client.get(
                self._config.api_url,
                params=all_params,
            )
        except httpx.TimeoutException as e:
            raise MediaWikiApiError("timeout", f"Request timeout: {e}") from e
        except httpx.RequestError as e:
            raise MediaWikiApiError("network", f"Request failed: {e}") from e

        content_length = response.headers.get("content-length")
        if content_length and int(content_length) > MAX_RESPONSE_SIZE:
            raise MediaWikiApiError("oversize", "Response too large")

        if not response.is_success:
            raise MediaWikiApiError(
                str(response.status_code),
                f"HTTP {response.status_code}",
            )

        data: dict[str, Any] = response.json()

        if "error" in data:
            self._handle_api_error(data["error"])

        return data

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

        data = await self._fetch_query(all_params)

        if max_pages <= 1 or "continue" not in data or not continue_key:
            return data

        return await self._fetch_continuation(all_params, data, max_pages)

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
        data = initial_data
        pages_fetched = 1

        while "continue" in data and pages_fetched < max_pages:
            next_params = {**all_params, **data["continue"]}
            try:
                data = await self._fetch_query(next_params)
            except (MediaWikiApiError, httpx.HTTPError):
                break

            page_query = data.get("query", {})
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
        client = await self._get_client()

        all_params = {
            "action": "parse",
            "format": "json",
            "formatversion": "2",
            **params,
        }

        try:
            response = await client.get(
                self._config.api_url,
                params=all_params,
            )
        except httpx.TimeoutException as e:
            raise MediaWikiApiError("timeout", f"Request timeout: {e}") from e
        except httpx.RequestError as e:
            raise MediaWikiApiError("network", f"Request failed: {e}") from e

        if not response.is_success:
            raise MediaWikiApiError(
                str(response.status_code),
                f"HTTP {response.status_code}",
            )

        data: dict[str, Any] = response.json()

        if "error" in data:
            self._handle_api_error(data["error"])

        return data

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

        client = await self._get_client()

        post_data = {
            "action": action,
            "format": "json",
            "formatversion": "2",
            **data,
        }

        if use_csrf:
            csrf_token = await self._get_csrf_token()
            post_data["token"] = csrf_token

        try:
            response = await client.post(
                self._config.api_url,
                data=post_data,
            )
        except httpx.TimeoutException as e:
            raise MediaWikiApiError("timeout", f"Request timeout: {e}") from e
        except httpx.RequestError as e:
            raise MediaWikiApiError("network", f"Request failed: {e}") from e

        if not response.is_success:
            raise MediaWikiApiError(
                str(response.status_code),
                f"HTTP {response.status_code}",
            )

        result: dict[str, Any] = response.json()

        if "error" in result:
            error_code = result["error"].get("code", "unknown")
            if error_code == "badtoken":
                self._csrf_token = None
                csrf_token = await self._get_csrf_token()
                post_data["token"] = csrf_token
                response = await client.post(
                    self._config.api_url,
                    data=post_data,
                )
                result = response.json()
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
