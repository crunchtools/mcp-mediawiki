"""Tests for MCP tools.

These tests verify tool behavior without making actual API calls.
Integration tests with a real MediaWiki instance should be run separately.
"""

from unittest.mock import AsyncMock, patch

import httpx
import pytest


class TestToolRegistration:
    """Tests to verify all tools are properly registered."""

    def test_server_has_tools(self) -> None:
        """Server should have all expected tools registered."""
        from mcp_mediawiki_crunchtools.server import mcp

        assert mcp is not None

    def test_imports(self) -> None:
        """All tool functions should be importable."""
        import mcp_mediawiki_crunchtools.tools as tools_mod
        from mcp_mediawiki_crunchtools.tools import __all__

        for name in __all__:
            func = getattr(tools_mod, name)
            assert callable(func), f"{name} is not callable"

    def test_tool_count(self) -> None:
        """Server should have exactly 19 tools registered."""
        from mcp_mediawiki_crunchtools.tools import __all__

        assert len(__all__) == 19


class TestErrorSafety:
    """Tests to verify error messages don't leak sensitive data."""

    def test_mediawiki_api_error_sanitizes_password(self) -> None:
        """MediaWikiApiError should sanitize passwords from messages."""
        import os

        from mcp_mediawiki_crunchtools.errors import MediaWikiApiError

        os.environ["MEDIAWIKI_PASSWORD"] = "super_secret_pass_123"

        try:
            error = MediaWikiApiError("auth", "Failed with super_secret_pass_123")
            assert "super_secret_pass_123" not in str(error)
            assert "***" in str(error)
        finally:
            del os.environ["MEDIAWIKI_PASSWORD"]

    def test_mediawiki_api_error_sanitizes_http_pass(self) -> None:
        """MediaWikiApiError should sanitize HTTP passwords from messages."""
        import os

        from mcp_mediawiki_crunchtools.errors import MediaWikiApiError

        os.environ["MEDIAWIKI_HTTP_PASS"] = "http_secret_456"

        try:
            error = MediaWikiApiError("auth", "Failed with http_secret_456")
            assert "http_secret_456" not in str(error)
            assert "***" in str(error)
        finally:
            del os.environ["MEDIAWIKI_HTTP_PASS"]

    def test_page_not_found_truncates_long_titles(self) -> None:
        """PageNotFoundError should truncate long titles."""
        from mcp_mediawiki_crunchtools.errors import PageNotFoundError

        long_title = "a" * 200
        error = PageNotFoundError(long_title)
        error_str = str(error)

        assert long_title not in error_str
        assert "..." in error_str


class TestConfigSafety:
    """Tests for configuration security."""

    def test_config_repr_hides_password(self) -> None:
        """Config repr should never show the password."""
        import os

        os.environ["MEDIAWIKI_URL"] = "https://example.com/w"
        os.environ["MEDIAWIKI_USERNAME"] = "testuser"
        os.environ["MEDIAWIKI_PASSWORD"] = "secret_password_789"

        try:
            from mcp_mediawiki_crunchtools.config import Config

            config = Config()
            assert "secret_password_789" not in repr(config)
            assert "secret_password_789" not in str(config)
            assert "***" in repr(config)
        finally:
            del os.environ["MEDIAWIKI_URL"]
            del os.environ["MEDIAWIKI_USERNAME"]
            del os.environ["MEDIAWIKI_PASSWORD"]

    def test_config_requires_url(self) -> None:
        """Config should require MEDIAWIKI_URL."""
        import os

        from mcp_mediawiki_crunchtools.config import Config
        from mcp_mediawiki_crunchtools.errors import ConfigurationError

        url = os.environ.pop("MEDIAWIKI_URL", None)

        try:
            import mcp_mediawiki_crunchtools.config as config_module

            config_module._config = None

            with pytest.raises(ConfigurationError):
                Config()
        finally:
            if url:
                os.environ["MEDIAWIKI_URL"] = url

    def test_config_api_url(self) -> None:
        """Config should derive api.php URL from wiki URL."""
        import os

        os.environ["MEDIAWIKI_URL"] = "https://example.com/w"

        try:
            from mcp_mediawiki_crunchtools.config import Config

            config = Config()
            assert config.api_url == "https://example.com/w/api.php"
            assert config.wiki_url == "https://example.com/w"
        finally:
            del os.environ["MEDIAWIKI_URL"]

    def test_config_strips_trailing_slash(self) -> None:
        """Config should strip trailing slash from URL."""
        import os

        os.environ["MEDIAWIKI_URL"] = "https://example.com/w/"

        try:
            from mcp_mediawiki_crunchtools.config import Config

            config = Config()
            assert config.api_url == "https://example.com/w/api.php"
        finally:
            del os.environ["MEDIAWIKI_URL"]

    def test_config_rejects_http(self) -> None:
        """Config should reject non-HTTPS URLs for non-localhost."""
        import os

        from mcp_mediawiki_crunchtools.config import Config
        from mcp_mediawiki_crunchtools.errors import ConfigurationError

        os.environ["MEDIAWIKI_URL"] = "http://example.com/w"

        try:
            with pytest.raises(ConfigurationError, match="HTTPS"):
                Config()
        finally:
            del os.environ["MEDIAWIKI_URL"]

    def test_config_allows_localhost_http(self) -> None:
        """Config should allow HTTP for localhost."""
        import os

        os.environ["MEDIAWIKI_URL"] = "http://localhost:8080/w"

        try:
            from mcp_mediawiki_crunchtools.config import Config

            config = Config()
            assert config.api_url == "http://localhost:8080/w/api.php"
        finally:
            del os.environ["MEDIAWIKI_URL"]

    def test_config_no_credentials(self) -> None:
        """Config should work without credentials (read-only mode)."""
        import os

        os.environ["MEDIAWIKI_URL"] = "https://en.wikipedia.org/w"
        os.environ.pop("MEDIAWIKI_USERNAME", None)
        os.environ.pop("MEDIAWIKI_PASSWORD", None)

        try:
            from mcp_mediawiki_crunchtools.config import Config

            config = Config()
            assert config.has_credentials is False
            assert config.username is None
            assert config.password is None
        finally:
            del os.environ["MEDIAWIKI_URL"]

    def test_config_requires_password_with_username(self) -> None:
        """Config should require password when username is set."""
        import os

        from mcp_mediawiki_crunchtools.config import Config
        from mcp_mediawiki_crunchtools.errors import ConfigurationError

        os.environ["MEDIAWIKI_URL"] = "https://example.com/w"
        os.environ["MEDIAWIKI_USERNAME"] = "testuser"
        os.environ.pop("MEDIAWIKI_PASSWORD", None)

        try:
            with pytest.raises(ConfigurationError, match="MEDIAWIKI_PASSWORD"):
                Config()
        finally:
            del os.environ["MEDIAWIKI_URL"]
            del os.environ["MEDIAWIKI_USERNAME"]

    def test_config_http_auth(self) -> None:
        """Config should support HTTP Basic Auth."""
        import os

        os.environ["MEDIAWIKI_URL"] = "https://example.com/w"
        os.environ["MEDIAWIKI_HTTP_USER"] = "httpuser"
        os.environ["MEDIAWIKI_HTTP_PASS"] = "httppass"

        try:
            from mcp_mediawiki_crunchtools.config import Config

            config = Config()
            assert config.http_auth == ("httpuser", "httppass")
        finally:
            del os.environ["MEDIAWIKI_URL"]
            del os.environ["MEDIAWIKI_HTTP_USER"]
            del os.environ["MEDIAWIKI_HTTP_PASS"]



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


@pytest.fixture(autouse=True)
def _reset_client_singleton():
    """Reset the global client and config singletons between tests."""
    import mcp_mediawiki_crunchtools.client as client_mod
    import mcp_mediawiki_crunchtools.config as config_mod

    client_mod._client = None
    config_mod._config = None
    yield
    client_mod._client = None
    config_mod._config = None


def _patch_client(mock_response: httpx.Response):
    """Patch the httpx AsyncClient to return a mock response.

    Sets MEDIAWIKI_URL so config initializes, then mocks the HTTP layer.
    """
    import os

    import mcp_mediawiki_crunchtools.client as client_mod
    import mcp_mediawiki_crunchtools.config as config_mod

    client_mod._client = None
    config_mod._config = None

    os.environ.setdefault("MEDIAWIKI_URL", "https://example.com/w")

    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.get = AsyncMock(return_value=mock_response)
    mock_http.post = AsyncMock(return_value=mock_response)

    return patch.object(
        httpx, "AsyncClient", return_value=mock_http,
    )



class TestPageTools:
    """Tests for page tools with mocked API responses."""

    async def test_search(self) -> None:
        """Search should return query results."""
        mock_resp = _mock_response(
            json_data={
                "query": {
                    "search": [
                        {"title": "Test Page", "snippet": "...test..."},
                    ],
                    "searchinfo": {"totalhits": 1},
                },
            },
        )

        with _patch_client(mock_resp):
            from mcp_mediawiki_crunchtools.tools import search

            result = await search(query="test")
            assert "query" in result
            assert "search" in result["query"]

    async def test_get_page(self) -> None:
        """Get page should return page content."""
        mock_resp = _mock_response(
            json_data={
                "query": {
                    "pages": [
                        {
                            "pageid": 1,
                            "title": "Main Page",
                            "revisions": [{"content": "Hello wiki"}],
                        },
                    ],
                },
            },
        )

        with _patch_client(mock_resp):
            from mcp_mediawiki_crunchtools.tools import get_page

            result = await get_page(title="Main Page")
            assert "query" in result
            assert "pages" in result["query"]

    async def test_get_page_html(self) -> None:
        """Get page HTML should return parsed content."""
        mock_resp = _mock_response(
            json_data={
                "parse": {
                    "title": "Main Page",
                    "text": "<p>Hello</p>",
                },
            },
        )

        with _patch_client(mock_resp):
            from mcp_mediawiki_crunchtools.tools import get_page_html

            result = await get_page_html(title="Main Page")
            assert "parse" in result

    async def test_list_pages(self) -> None:
        """List pages should return allpages results."""
        mock_resp = _mock_response(
            json_data={
                "query": {
                    "allpages": [
                        {"pageid": 1, "title": "Page A"},
                        {"pageid": 2, "title": "Page B"},
                    ],
                },
            },
        )

        with _patch_client(mock_resp):
            from mcp_mediawiki_crunchtools.tools import list_pages

            result = await list_pages()
            assert "query" in result
            assert "allpages" in result["query"]

    async def test_create_page(self) -> None:
        """Create page should POST with createonly flag."""
        login_needtoken_resp = _mock_response(
            json_data={
                "login": {"result": "NeedToken", "token": "abc123+\\"},
            },
        )
        login_success_resp = _mock_response(
            json_data={
                "login": {"result": "Success", "lgusername": "testuser"},
            },
        )
        csrf_token_resp = _mock_response(
            json_data={
                "query": {"tokens": {"csrftoken": "csrf456+\\"}},
            },
        )
        edit_resp = _mock_response(
            json_data={
                "edit": {"result": "Success", "pageid": 42, "title": "New Page"},
            },
        )

        import os

        os.environ["MEDIAWIKI_URL"] = "https://example.com/w"
        os.environ["MEDIAWIKI_USERNAME"] = "testuser"
        os.environ["MEDIAWIKI_PASSWORD"] = "testpass"

        try:
            mock_http = AsyncMock(spec=httpx.AsyncClient)
            mock_http.get = AsyncMock(
                side_effect=[csrf_token_resp],
            )
            mock_http.post = AsyncMock(
                side_effect=[login_needtoken_resp, login_success_resp, edit_resp],
            )

            with patch.object(httpx, "AsyncClient", return_value=mock_http):
                import mcp_mediawiki_crunchtools.client as client_mod
                import mcp_mediawiki_crunchtools.config as config_mod

                client_mod._client = None
                config_mod._config = None

                from mcp_mediawiki_crunchtools.tools import create_page

                result = await create_page(
                    title="New Page", content="Hello world",
                )
                assert "edit" in result
                assert result["edit"]["result"] == "Success"
        finally:
            del os.environ["MEDIAWIKI_USERNAME"]
            del os.environ["MEDIAWIKI_PASSWORD"]

    async def test_edit_page(self) -> None:
        """Edit page should POST content."""
        login_needtoken_resp = _mock_response(
            json_data={
                "login": {"result": "NeedToken", "token": "abc123+\\"},
            },
        )
        login_success_resp = _mock_response(
            json_data={
                "login": {"result": "Success", "lgusername": "testuser"},
            },
        )
        csrf_token_resp = _mock_response(
            json_data={
                "query": {"tokens": {"csrftoken": "csrf456+\\"}},
            },
        )
        edit_resp = _mock_response(
            json_data={
                "edit": {"result": "Success", "pageid": 1, "title": "Test"},
            },
        )

        import os

        os.environ["MEDIAWIKI_URL"] = "https://example.com/w"
        os.environ["MEDIAWIKI_USERNAME"] = "testuser"
        os.environ["MEDIAWIKI_PASSWORD"] = "testpass"

        try:
            mock_http = AsyncMock(spec=httpx.AsyncClient)
            mock_http.get = AsyncMock(
                side_effect=[csrf_token_resp],
            )
            mock_http.post = AsyncMock(
                side_effect=[login_needtoken_resp, login_success_resp, edit_resp],
            )

            with patch.object(httpx, "AsyncClient", return_value=mock_http):
                import mcp_mediawiki_crunchtools.client as client_mod
                import mcp_mediawiki_crunchtools.config as config_mod

                client_mod._client = None
                config_mod._config = None

                from mcp_mediawiki_crunchtools.tools import edit_page

                result = await edit_page(
                    title="Test", content="Updated content",
                )
                assert "edit" in result

        finally:
            del os.environ["MEDIAWIKI_USERNAME"]
            del os.environ["MEDIAWIKI_PASSWORD"]



class TestCategoryTools:
    """Tests for category tools."""

    async def test_list_categories(self) -> None:
        """List categories should return allcategories."""
        mock_resp = _mock_response(
            json_data={
                "query": {
                    "allcategories": [
                        {"category": "Cats"},
                        {"category": "Dogs"},
                    ],
                },
            },
        )

        with _patch_client(mock_resp):
            from mcp_mediawiki_crunchtools.tools import list_categories

            result = await list_categories()
            assert "query" in result
            assert "allcategories" in result["query"]

    async def test_get_category_members(self) -> None:
        """Get category members should return pages in category."""
        mock_resp = _mock_response(
            json_data={
                "query": {
                    "categorymembers": [
                        {"pageid": 1, "title": "Member 1"},
                    ],
                },
            },
        )

        with _patch_client(mock_resp):
            from mcp_mediawiki_crunchtools.tools import get_category_members

            result = await get_category_members(category="TestCategory")
            assert "query" in result
            assert "categorymembers" in result["query"]

    async def test_get_page_categories(self) -> None:
        """Get page categories should return categories for a page."""
        mock_resp = _mock_response(
            json_data={
                "query": {
                    "pages": [
                        {
                            "pageid": 1,
                            "title": "Test",
                            "categories": [{"title": "Category:Test"}],
                        },
                    ],
                },
            },
        )

        with _patch_client(mock_resp):
            from mcp_mediawiki_crunchtools.tools import get_page_categories

            result = await get_page_categories(title="Test")
            assert "query" in result



class TestRecentChanges:
    """Tests for recent changes tool."""

    async def test_list_recent_changes(self) -> None:
        """List recent changes should return recent edits."""
        mock_resp = _mock_response(
            json_data={
                "query": {
                    "recentchanges": [
                        {"type": "edit", "title": "Main Page", "user": "Admin"},
                    ],
                },
            },
        )

        with _patch_client(mock_resp):
            from mcp_mediawiki_crunchtools.tools import list_recent_changes

            result = await list_recent_changes()
            assert "query" in result
            assert "recentchanges" in result["query"]


class TestParsingTools:
    """Tests for parsing tool."""

    async def test_parse_wikitext(self) -> None:
        """Parse wikitext should return HTML."""
        mock_resp = _mock_response(
            json_data={
                "parse": {
                    "text": "<p>Hello <b>world</b></p>",
                },
            },
        )

        with _patch_client(mock_resp):
            from mcp_mediawiki_crunchtools.tools import parse_wikitext

            result = await parse_wikitext(wikitext="Hello '''world'''")
            assert "parse" in result


class TestSiteInfoTools:
    """Tests for site info tools."""

    async def test_get_site_info(self) -> None:
        """Get site info should return wiki configuration."""
        mock_resp = _mock_response(
            json_data={
                "query": {
                    "general": {
                        "sitename": "Test Wiki",
                        "generator": "MediaWiki 1.42",
                    },
                    "statistics": {"pages": 100, "articles": 50},
                },
            },
        )

        with _patch_client(mock_resp):
            from mcp_mediawiki_crunchtools.tools import get_site_info

            result = await get_site_info()
            assert "query" in result

    async def test_list_namespaces(self) -> None:
        """List namespaces should return namespace definitions."""
        mock_resp = _mock_response(
            json_data={
                "query": {
                    "namespaces": {
                        "0": {"id": 0, "name": ""},
                        "1": {"id": 1, "name": "Talk"},
                    },
                },
            },
        )

        with _patch_client(mock_resp):
            from mcp_mediawiki_crunchtools.tools import list_namespaces

            result = await list_namespaces()
            assert "query" in result


class TestUserTools:
    """Tests for user tools."""

    async def test_get_user_info(self) -> None:
        """Get user info should return user details."""
        mock_resp = _mock_response(
            json_data={
                "query": {
                    "users": [
                        {
                            "name": "TestUser",
                            "editcount": 42,
                            "registration": "2024-01-01T00:00:00Z",
                        },
                    ],
                },
            },
        )

        with _patch_client(mock_resp):
            from mcp_mediawiki_crunchtools.tools import get_user_info

            result = await get_user_info(username="TestUser")
            assert "query" in result
            assert "users" in result["query"]

    async def test_list_user_contributions(self) -> None:
        """List user contributions should return edits."""
        mock_resp = _mock_response(
            json_data={
                "query": {
                    "usercontribs": [
                        {"title": "Test Page", "timestamp": "2024-01-01T00:00:00Z"},
                    ],
                },
            },
        )

        with _patch_client(mock_resp):
            from mcp_mediawiki_crunchtools.tools import list_user_contributions

            result = await list_user_contributions(username="TestUser")
            assert "query" in result
            assert "usercontribs" in result["query"]


class TestFileTools:
    """Tests for file tools."""

    async def test_get_file_info(self) -> None:
        """Get file info should return file metadata."""
        mock_resp = _mock_response(
            json_data={
                "query": {
                    "pages": [
                        {
                            "pageid": 10,
                            "title": "File:Test.png",
                            "imageinfo": [
                                {"url": "https://example.com/Test.png", "size": 12345},
                            ],
                        },
                    ],
                },
            },
        )

        with _patch_client(mock_resp):
            from mcp_mediawiki_crunchtools.tools import get_file_info

            result = await get_file_info(filename="Test.png")
            assert "query" in result

    async def test_list_files(self) -> None:
        """List files should return file listing."""
        mock_resp = _mock_response(
            json_data={
                "query": {
                    "allimages": [
                        {"name": "Test.png", "url": "https://example.com/Test.png"},
                    ],
                },
            },
        )

        with _patch_client(mock_resp):
            from mcp_mediawiki_crunchtools.tools import list_files

            result = await list_files()
            assert "query" in result
            assert "allimages" in result["query"]



class TestClientErrorHandling:
    """Tests for client error handling."""

    async def test_page_not_found_error(self) -> None:
        """Client should raise PageNotFoundError for missing pages."""
        mock_resp = _mock_response(
            json_data={
                "error": {
                    "code": "missingtitle",
                    "info": "The page you specified doesn't exist.",
                },
            },
        )

        with _patch_client(mock_resp):
            from mcp_mediawiki_crunchtools.errors import PageNotFoundError
            from mcp_mediawiki_crunchtools.tools import get_page

            with pytest.raises(PageNotFoundError):
                await get_page(title="Nonexistent Page")

    async def test_permission_denied_error(self) -> None:
        """Client should raise PermissionDeniedError for protected pages."""
        mock_resp = _mock_response(
            json_data={
                "error": {
                    "code": "protectedpage",
                    "info": "This page is protected.",
                },
            },
        )

        with _patch_client(mock_resp):
            from mcp_mediawiki_crunchtools.errors import PermissionDeniedError
            from mcp_mediawiki_crunchtools.tools import get_page

            with pytest.raises(PermissionDeniedError):
                await get_page(title="Protected Page")

    async def test_rate_limit_error(self) -> None:
        """Client should raise RateLimitError."""
        mock_resp = _mock_response(
            json_data={
                "error": {
                    "code": "ratelimited",
                    "info": "You've exceeded your rate limit.",
                },
            },
        )

        with _patch_client(mock_resp):
            from mcp_mediawiki_crunchtools.errors import RateLimitError
            from mcp_mediawiki_crunchtools.tools import get_page

            with pytest.raises(RateLimitError):
                await get_page(title="Any Page")
