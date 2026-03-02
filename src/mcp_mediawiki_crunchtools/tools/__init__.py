"""MediaWiki MCP tools.

This package contains all the MCP tool implementations for MediaWiki operations.
"""

from .categories import get_category_members, get_page_categories, list_categories
from .files import get_file_info, list_files
from .pages import (
    create_page,
    delete_page,
    edit_page,
    get_page,
    get_page_html,
    list_pages,
    move_page,
    search,
)
from .parsing import parse_wikitext
from .recent_changes import list_recent_changes
from .site_info import get_site_info, list_namespaces
from .users import get_user_info, list_user_contributions

__all__ = [
    "search",
    "get_page",
    "get_page_html",
    "list_pages",
    "create_page",
    "edit_page",
    "delete_page",
    "move_page",
    "list_categories",
    "get_category_members",
    "get_page_categories",
    "list_recent_changes",
    "parse_wikitext",
    "get_site_info",
    "list_namespaces",
    "get_user_info",
    "list_user_contributions",
    "get_file_info",
    "list_files",
]
