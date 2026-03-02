"""Secure configuration handling.

This module handles all configuration including sensitive credentials.
Passwords are stored as SecretStr to prevent accidental logging.
"""

import logging
import os
from urllib.parse import urlparse

from pydantic import SecretStr

from .errors import ConfigurationError

logger = logging.getLogger(__name__)


class Config:
    """Secure configuration for MediaWiki API access.

    Credentials are stored as SecretStr and should only be accessed
    via properties when actually needed for API calls.
    """

    def __init__(self) -> None:
        """Initialize configuration from environment variables.

        Raises:
            ConfigurationError: If required environment variables are missing or invalid.
        """
        wiki_url = os.environ.get("MEDIAWIKI_URL")
        if not wiki_url:
            raise ConfigurationError(
                "MEDIAWIKI_URL environment variable required. "
                "Set to your wiki's base URL (e.g., https://en.wikipedia.org/w/)"
            )

        wiki_url = wiki_url.rstrip("/")

        parsed = urlparse(wiki_url)
        if not parsed.scheme or not parsed.netloc:
            raise ConfigurationError(
                "Invalid MEDIAWIKI_URL: must be a valid URL "
                "(e.g., https://en.wikipedia.org/w/)"
            )

        if parsed.scheme != "https" and parsed.hostname not in (
            "localhost", "127.0.0.1", "::1",
        ):
            raise ConfigurationError(
                "MEDIAWIKI_URL must use HTTPS for non-localhost URLs"
            )

        self._wiki_url = wiki_url

        username = os.environ.get("MEDIAWIKI_USERNAME")
        password = os.environ.get("MEDIAWIKI_PASSWORD")

        self._username = username
        self._password = SecretStr(password) if password else None

        if username and not password:
            raise ConfigurationError(
                "MEDIAWIKI_PASSWORD required when MEDIAWIKI_USERNAME is set"
            )

        http_user = os.environ.get("MEDIAWIKI_HTTP_USER")
        http_pass = os.environ.get("MEDIAWIKI_HTTP_PASS")

        self._http_user = http_user
        self._http_pass = SecretStr(http_pass) if http_pass else None

        if http_user and not http_pass:
            raise ConfigurationError(
                "MEDIAWIKI_HTTP_PASS required when MEDIAWIKI_HTTP_USER is set"
            )

        logger.info("Configuration loaded successfully (Wiki: %s)", self._wiki_url)

    @property
    def api_url(self) -> str:
        """MediaWiki API endpoint URL (api.php)."""
        return f"{self._wiki_url}/api.php"

    @property
    def wiki_url(self) -> str:
        """Wiki base URL."""
        return self._wiki_url

    @property
    def username(self) -> str | None:
        """MediaWiki username for authentication."""
        return self._username

    @property
    def password(self) -> str | None:
        """Get password value for API calls. Use sparingly."""
        if self._password is None:
            return None
        return self._password.get_secret_value()

    @property
    def has_credentials(self) -> bool:
        """Whether wiki login credentials are configured."""
        return self._username is not None and self._password is not None

    @property
    def http_auth(self) -> tuple[str, str] | None:
        """HTTP Basic Auth tuple for .htaccess-protected wikis."""
        if self._http_user and self._http_pass:
            return (self._http_user, self._http_pass.get_secret_value())
        return None

    def __repr__(self) -> str:
        """Safe repr that never exposes credentials."""
        return f"Config(wiki_url={self._wiki_url}, username={self._username}, password=***)"

    def __str__(self) -> str:
        """Safe str that never exposes credentials."""
        return f"Config(wiki_url={self._wiki_url}, username={self._username}, password=***)"


_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance.

    This function lazily initializes the configuration on first call.
    Subsequent calls return the same instance.

    Returns:
        The global Config instance.

    Raises:
        ConfigurationError: If configuration is invalid.
    """
    global _config
    if _config is None:
        _config = Config()
    return _config
