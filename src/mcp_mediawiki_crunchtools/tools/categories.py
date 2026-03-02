"""Category management tools.

Tools for listing categories, getting category members, and page categories.
"""

from typing import Any

from ..client import get_client
from ..models import validate_page_title


async def list_categories(
    prefix: str | None = None,
    limit: int = 50,
    from_name: str | None = None,
) -> dict[str, Any]:
    """List all categories on the wiki.

    Args:
        prefix: Filter categories starting with this prefix.
        limit: Maximum results (default: 50, max: 500).
        from_name: Start listing from this category (for pagination).

    Returns:
        List of category names with metadata.
    """
    client = get_client()

    params: dict[str, Any] = {
        "list": "allcategories",
        "aclimit": min(limit, 500),
    }

    if prefix:
        params["acprefix"] = prefix
    if from_name:
        params["acfrom"] = from_name

    return await client.query(params=params)


async def get_category_members(
    category: str,
    member_type: str | None = None,
    limit: int = 50,
    continue_from: str | None = None,
) -> dict[str, Any]:
    """Get pages in a category.

    Args:
        category: Category name (with or without "Category:" prefix).
        member_type: Filter by type: page, subcat, file (default: all).
        limit: Maximum results (default: 50, max: 500).
        continue_from: Continue token for pagination.

    Returns:
        List of category members with titles and types.
    """
    if not category.startswith("Category:"):
        category = f"Category:{category}"
    validate_page_title(category)

    client = get_client()

    params: dict[str, Any] = {
        "list": "categorymembers",
        "cmtitle": category,
        "cmlimit": min(limit, 500),
        "cmprop": "ids|title|type|timestamp",
    }

    if member_type:
        params["cmtype"] = member_type
    if continue_from:
        params["cmcontinue"] = continue_from

    return await client.query(params=params)


async def get_page_categories(
    title: str,
    limit: int = 50,
    show_hidden: bool = False,
) -> dict[str, Any]:
    """Get categories that a page belongs to.

    Args:
        title: Page title.
        limit: Maximum categories to return (default: 50, max: 500).
        show_hidden: Include hidden categories (default: False).

    Returns:
        List of categories the page belongs to.
    """
    validated_title = validate_page_title(title)
    client = get_client()

    params: dict[str, Any] = {
        "titles": validated_title,
        "prop": "categories",
        "cllimit": min(limit, 500),
    }

    if show_hidden:
        params["clshow"] = "hidden"

    return await client.query(params=params)
