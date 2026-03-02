"""Page management tools.

Tools for searching, reading, creating, editing, deleting, and moving wiki pages.
"""

from typing import Any

from ..client import get_client
from ..models import CreatePageInput, EditPageInput, MovePageInput, validate_page_title


async def search(
    query: str,
    namespace: int = 0,
    limit: int = 10,
) -> dict[str, Any]:
    """Full-text search across the wiki.

    Args:
        query: Search query string.
        namespace: Namespace to search in (0=Main, default: 0).
        limit: Maximum results to return (default: 10, max: 50).

    Returns:
        Search results with titles, snippets, and metadata.
    """
    if not query or not query.strip():
        raise ValueError("Search query must not be empty")

    client = get_client()
    return await client.query(
        params={
            "list": "search",
            "srsearch": query.strip(),
            "srnamespace": namespace,
            "srlimit": min(limit, 50),
            "srprop": "snippet|titlesnippet|size|wordcount|timestamp",
        },
    )


async def get_page(
    title: str,
) -> dict[str, Any]:
    """Get page wikitext content.

    Args:
        title: Page title (e.g., "Main Page").

    Returns:
        Page content, revision info, and metadata.
    """
    validated_title = validate_page_title(title)
    client = get_client()
    return await client.query(
        params={
            "titles": validated_title,
            "prop": "revisions|info",
            "rvprop": "content|timestamp|user|comment|ids",
            "rvslots": "main",
        },
    )


async def get_page_html(
    title: str,
) -> dict[str, Any]:
    """Parse a page to HTML.

    Args:
        title: Page title to parse.

    Returns:
        Parsed HTML content and page properties.
    """
    validated_title = validate_page_title(title)
    client = get_client()
    return await client.parse(
        params={
            "page": validated_title,
            "prop": "text|categories|links|sections",
        },
    )


async def list_pages(
    prefix: str | None = None,
    namespace: int = 0,
    limit: int = 50,
    from_title: str | None = None,
) -> dict[str, Any]:
    """List pages with optional prefix filter.

    Args:
        prefix: Filter pages starting with this prefix.
        namespace: Namespace to list (0=Main, default: 0).
        limit: Maximum results (default: 50, max: 500).
        from_title: Start listing from this title (for pagination).

    Returns:
        List of page titles with metadata.
    """
    client = get_client()

    params: dict[str, Any] = {
        "list": "allpages",
        "apnamespace": namespace,
        "aplimit": min(limit, 500),
    }

    if prefix:
        params["apprefix"] = prefix
    if from_title:
        params["apfrom"] = from_title

    return await client.query(params=params)


async def create_page(
    title: str,
    content: str,
    summary: str = "",
) -> dict[str, Any]:
    """Create a new wiki page.

    Args:
        title: Page title.
        content: Page wikitext content.
        summary: Edit summary (default: empty).

    Returns:
        Creation result with page info.
    """
    validated = CreatePageInput(title=title, content=content, summary=summary)

    client = get_client()

    post_data: dict[str, Any] = {
        "title": validated.title,
        "text": validated.content,
        "createonly": "1",
    }
    if validated.summary:
        post_data["summary"] = validated.summary

    return await client.post_action("edit", post_data)


async def edit_page(
    title: str,
    content: str,
    summary: str = "",
    minor: bool = False,
) -> dict[str, Any]:
    """Edit an existing wiki page.

    Args:
        title: Page title.
        content: New page wikitext content.
        summary: Edit summary (default: empty).
        minor: Mark as minor edit (default: False).

    Returns:
        Edit result with revision info.
    """
    validated = EditPageInput(
        title=title, content=content, summary=summary, minor=minor,
    )

    client = get_client()

    post_data: dict[str, Any] = {
        "title": validated.title,
        "text": validated.content,
    }
    if validated.summary:
        post_data["summary"] = validated.summary
    if validated.minor:
        post_data["minor"] = "1"

    return await client.post_action("edit", post_data)


async def delete_page(
    title: str,
    reason: str = "",
) -> dict[str, Any]:
    """Delete a wiki page.

    Args:
        title: Page title to delete.
        reason: Reason for deletion (default: empty).

    Returns:
        Deletion result.
    """
    validated_title = validate_page_title(title)

    client = get_client()

    post_data: dict[str, Any] = {"title": validated_title}
    if reason:
        post_data["reason"] = reason

    return await client.post_action("delete", post_data)


async def move_page(
    from_title: str,
    to_title: str,
    reason: str = "",
    move_talk: bool = True,
    no_redirect: bool = False,
) -> dict[str, Any]:
    """Move (rename) a wiki page.

    Args:
        from_title: Current page title.
        to_title: New page title.
        reason: Reason for move (default: empty).
        move_talk: Also move the talk page (default: True).
        no_redirect: Do not create a redirect (default: False).

    Returns:
        Move result with old and new titles.
    """
    validated = MovePageInput(
        from_title=from_title,
        to_title=to_title,
        reason=reason,
        move_talk=move_talk,
        no_redirect=no_redirect,
    )

    client = get_client()

    post_data: dict[str, Any] = {
        "from": validated.from_title,
        "to": validated.to_title,
    }
    if validated.reason:
        post_data["reason"] = validated.reason
    if validated.move_talk:
        post_data["movetalk"] = "1"
    if validated.no_redirect:
        post_data["noredirect"] = "1"

    return await client.post_action("move", post_data)
