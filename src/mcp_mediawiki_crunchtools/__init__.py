"""MCP MediaWiki CrunchTools - Secure MCP server for MediaWiki.

A security-focused MCP server for MediaWiki wikis — search, pages,
categories, recent changes, and more. Works with any MediaWiki instance
(public or private, including Wikipedia and self-hosted wikis).

Usage:
    mcp-mediawiki-crunchtools

    python -m mcp_mediawiki_crunchtools

    uvx mcp-mediawiki-crunchtools

Environment Variables:
    MEDIAWIKI_URL: Required. Wiki base URL (e.g., https://learn.fatherlinux.com/w/).
    MEDIAWIKI_USERNAME: Optional. Bot/user account for write operations.
    MEDIAWIKI_PASSWORD: Optional. Bot/user password.
    MEDIAWIKI_HTTP_USER: Optional. HTTP Basic Auth username (.htaccess).
    MEDIAWIKI_HTTP_PASS: Optional. HTTP Basic Auth password.

Example with Claude Code:
    claude mcp add mcp-mediawiki-crunchtools \\
        --env MEDIAWIKI_URL=https://en.wikipedia.org/w/ \\
        -- uvx mcp-mediawiki-crunchtools
"""

import argparse

from .server import mcp

__version__ = "0.1.0"
__all__ = ["main", "mcp"]


def main() -> None:
    """Main entry point for the MCP server."""
    parser = argparse.ArgumentParser(description="MCP server for MediaWiki")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to for HTTP transports (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8016,
        help="Port to bind to for HTTP transports (default: 8016)",
    )
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run()
    else:
        mcp.run(transport=args.transport, host=args.host, port=args.port)
