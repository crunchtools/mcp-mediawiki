"""Safe error types that can be shown to users.

This module defines exception classes that are safe to expose to MCP clients.
Internal errors should be caught and converted to UserError before propagating.
"""

SAFE_ID_MAX_LENGTH = 80


class UserError(Exception):
    """Base class for safe errors that can be shown to users.

    All error messages in UserError subclasses must be carefully crafted
    to avoid leaking sensitive information like passwords or internal paths.
    """

    pass


class ConfigurationError(UserError):
    """Error in server configuration."""

    pass


class MediaWikiApiError(UserError):
    """Error from MediaWiki API.

    The message is sanitized to remove any potential credential references.
    """

    def __init__(self, code: str, message: str) -> None:
        import os

        password = os.environ.get("MEDIAWIKI_PASSWORD", "")
        safe_message = message.replace(password, "***") if password else message
        http_pass = os.environ.get("MEDIAWIKI_HTTP_PASS", "")
        if http_pass:
            safe_message = safe_message.replace(http_pass, "***")
        super().__init__(f"MediaWiki API error ({code}): {safe_message}")


class PageNotFoundError(UserError):
    """Page not found on the wiki."""

    def __init__(self, title: str) -> None:
        if len(title) > SAFE_ID_MAX_LENGTH:
            safe_title = title[:SAFE_ID_MAX_LENGTH] + "..."
        else:
            safe_title = title
        super().__init__(f"Page not found: {safe_title}")


class PermissionDeniedError(UserError):
    """Permission denied for the requested operation."""

    def __init__(self, detail: str) -> None:
        super().__init__(f"Permission denied: {detail}")


class RateLimitError(UserError):
    """Rate limit exceeded."""

    def __init__(self, retry_after: int | None = None) -> None:
        msg = "Rate limit exceeded."
        if retry_after:
            msg += f" Retry after {retry_after} seconds."
        super().__init__(msg)


class AuthenticationError(UserError):
    """Authentication failed."""

    def __init__(self, detail: str = "Login failed") -> None:
        super().__init__(f"Authentication error: {detail}")


class ValidationError(UserError):
    """Input validation error."""

    pass
