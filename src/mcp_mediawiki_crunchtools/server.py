"""FastMCP server setup for MediaWiki MCP.

This module creates and configures the MCP server with all tools.
"""

import logging
from typing import Any

from fastmcp import FastMCP

from .tools import (
    create_page,
    delete_page,
    edit_page,
    get_category_members,
    get_file_info,
    get_page,
    get_page_categories,
    get_page_html,
    get_site_info,
    get_user_info,
    list_categories,
    list_files,
    list_namespaces,
    list_pages,
    list_recent_changes,
    list_user_contributions,
    move_page,
    parse_wikitext,
    search,
)

logger = logging.getLogger(__name__)

mcp = FastMCP(
    name="mcp-mediawiki-crunchtools",
    version="0.1.3",
    instructions=(
        "Secure MCP server for MediaWiki wikis. Search, read, create, edit, "
        "and manage wiki pages, categories, files, and more. Works with any "
        "MediaWiki instance (public or private)."
    ),
)


@mcp.tool()
async def search_tool(
    query: str,
    namespace: int = 0,
    limit: int = 10,
) -> dict[str, Any]:
    """Full-text search across the wiki.

    Args:
        query: Search query string
        namespace: Namespace to search in (0=Main, default: 0)
        limit: Maximum results to return (default: 10, max: 50)

    Returns:
        Search results with titles, snippets, and metadata
    """
    return await search(query=query, namespace=namespace, limit=limit)


@mcp.tool()
async def get_page_tool(
    title: str,
) -> dict[str, Any]:
    """Get page wikitext content by title.

    Args:
        title: Page title (e.g., "Main Page")

    Returns:
        Page content, revision info, and metadata
    """
    return await get_page(title=title)


@mcp.tool()
async def get_page_html_tool(
    title: str,
) -> dict[str, Any]:
    """Parse a wiki page to HTML.

    Args:
        title: Page title to parse

    Returns:
        Parsed HTML content, categories, links, and sections
    """
    return await get_page_html(title=title)


@mcp.tool()
async def list_pages_tool(
    prefix: str | None = None,
    namespace: int = 0,
    limit: int = 50,
    from_title: str | None = None,
) -> dict[str, Any]:
    """List wiki pages with optional prefix filter.

    Args:
        prefix: Filter pages starting with this prefix
        namespace: Namespace to list (0=Main, default: 0)
        limit: Maximum results (default: 50, max: 500)
        from_title: Start listing from this title (for pagination)

    Returns:
        List of page titles with metadata
    """
    return await list_pages(
        prefix=prefix, namespace=namespace, limit=limit, from_title=from_title,
    )


@mcp.tool()
async def create_page_tool(
    title: str,
    content: str,
    summary: str = "",
) -> dict[str, Any]:
    """Create a new wiki page. Requires authentication.

    Args:
        title: Page title
        content: Page wikitext content
        summary: Edit summary (default: empty)

    Returns:
        Creation result with page info
    """
    return await create_page(title=title, content=content, summary=summary)


@mcp.tool()
async def edit_page_tool(
    title: str,
    content: str,
    summary: str = "",
    minor: bool = False,
) -> dict[str, Any]:
    """Edit an existing wiki page. Requires authentication.

    Args:
        title: Page title
        content: New page wikitext content
        summary: Edit summary (default: empty)
        minor: Mark as minor edit (default: False)

    Returns:
        Edit result with revision info
    """
    return await edit_page(
        title=title, content=content, summary=summary, minor=minor,
    )


@mcp.tool()
async def delete_page_tool(
    title: str,
    reason: str = "",
) -> dict[str, Any]:
    """Delete a wiki page. Requires admin authentication.

    Args:
        title: Page title to delete
        reason: Reason for deletion (default: empty)

    Returns:
        Deletion result
    """
    return await delete_page(title=title, reason=reason)


@mcp.tool()
async def move_page_tool(
    from_title: str,
    to_title: str,
    reason: str = "",
    move_talk: bool = True,
    no_redirect: bool = False,
) -> dict[str, Any]:
    """Move (rename) a wiki page. Requires authentication.

    Args:
        from_title: Current page title
        to_title: New page title
        reason: Reason for move (default: empty)
        move_talk: Also move the talk page (default: True)
        no_redirect: Do not create a redirect (default: False)

    Returns:
        Move result with old and new titles
    """
    return await move_page(
        from_title=from_title, to_title=to_title, reason=reason,
        move_talk=move_talk, no_redirect=no_redirect,
    )



@mcp.tool()
async def list_categories_tool(
    prefix: str | None = None,
    limit: int = 50,
    from_name: str | None = None,
) -> dict[str, Any]:
    """List all categories on the wiki.

    Args:
        prefix: Filter categories starting with this prefix
        limit: Maximum results (default: 50, max: 500)
        from_name: Start listing from this category (for pagination)

    Returns:
        List of category names with metadata
    """
    return await list_categories(
        prefix=prefix, limit=limit, from_name=from_name,
    )


@mcp.tool()
async def get_category_members_tool(
    category: str,
    member_type: str | None = None,
    limit: int = 50,
    continue_from: str | None = None,
) -> dict[str, Any]:
    """Get pages in a category.

    Args:
        category: Category name (with or without "Category:" prefix)
        member_type: Filter by type: page, subcat, file (default: all)
        limit: Maximum results (default: 50, max: 500)
        continue_from: Continue token for pagination

    Returns:
        List of category members with titles and types
    """
    return await get_category_members(
        category=category, member_type=member_type,
        limit=limit, continue_from=continue_from,
    )


@mcp.tool()
async def get_page_categories_tool(
    title: str,
    limit: int = 50,
    show_hidden: bool = False,
) -> dict[str, Any]:
    """Get categories that a page belongs to.

    Args:
        title: Page title
        limit: Maximum categories to return (default: 50, max: 500)
        show_hidden: Include hidden categories (default: False)

    Returns:
        List of categories the page belongs to
    """
    return await get_page_categories(
        title=title, limit=limit, show_hidden=show_hidden,
    )



@mcp.tool()
async def list_recent_changes_tool(
    namespace: int | None = None,
    limit: int = 50,
    tag: str | None = None,
    change_type: str | None = None,
    from_timestamp: str | None = None,
) -> dict[str, Any]:
    """List recent edits on the wiki.

    Args:
        namespace: Filter by namespace (default: all namespaces)
        limit: Maximum results (default: 50, max: 500)
        tag: Filter by tag name
        change_type: Filter by type: edit, new, log, categorize, external
        from_timestamp: Start from this timestamp (ISO 8601)

    Returns:
        List of recent changes with user, title, timestamp, and comment
    """
    return await list_recent_changes(
        namespace=namespace, limit=limit, tag=tag,
        change_type=change_type, from_timestamp=from_timestamp,
    )



@mcp.tool()
async def parse_wikitext_tool(
    wikitext: str,
    title: str | None = None,
) -> dict[str, Any]:
    """Parse raw wikitext to HTML.

    Args:
        wikitext: Raw wikitext content to parse
        title: Context page title for template resolution (optional)

    Returns:
        Parsed HTML output
    """
    return await parse_wikitext(wikitext=wikitext, title=title)



@mcp.tool()
async def get_site_info_tool() -> dict[str, Any]:
    """Get wiki configuration and version info.

    Returns:
        Site info including wiki name, version, base URL, and features
    """
    return await get_site_info()


@mcp.tool()
async def list_namespaces_tool() -> dict[str, Any]:
    """List all namespaces on the wiki.

    Returns:
        List of namespaces with IDs, names, and canonical names
    """
    return await list_namespaces()



@mcp.tool()
async def get_user_info_tool(
    username: str,
) -> dict[str, Any]:
    """Get user details from the wiki.

    Args:
        username: Username to look up

    Returns:
        User details including edit count, registration date, and groups
    """
    return await get_user_info(username=username)


@mcp.tool()
async def list_user_contributions_tool(
    username: str,
    namespace: int | None = None,
    limit: int = 50,
    from_timestamp: str | None = None,
) -> dict[str, Any]:
    """List edits by a user.

    Args:
        username: Username whose contributions to list
        namespace: Filter by namespace (default: all)
        limit: Maximum results (default: 50, max: 500)
        from_timestamp: Start from this timestamp (ISO 8601)

    Returns:
        List of user contributions with titles, timestamps, and comments
    """
    return await list_user_contributions(
        username=username, namespace=namespace,
        limit=limit, from_timestamp=from_timestamp,
    )



@mcp.tool()
async def get_file_info_tool(
    filename: str,
) -> dict[str, Any]:
    """Get file/image metadata from the wiki.

    Args:
        filename: File name (with or without "File:" prefix)

    Returns:
        File metadata including URL, size, dimensions, and MIME type
    """
    return await get_file_info(filename=filename)


@mcp.tool()
async def list_files_tool(
    prefix: str | None = None,
    limit: int = 50,
    mime_type: str | None = None,
    from_name: str | None = None,
) -> dict[str, Any]:
    """List files on the wiki.

    Args:
        prefix: Filter files starting with this prefix
        limit: Maximum results (default: 50, max: 500)
        mime_type: Filter by MIME type (e.g., "image/png")
        from_name: Start listing from this file (for pagination)

    Returns:
        List of files with metadata
    """
    return await list_files(
        prefix=prefix, limit=limit, mime_type=mime_type, from_name=from_name,
    )
