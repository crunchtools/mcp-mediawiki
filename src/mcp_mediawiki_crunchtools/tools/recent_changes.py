"""Recent changes tools.

Tools for listing recent edits on the wiki.
"""

from typing import Any

from ..client import get_client


async def list_recent_changes(
    namespace: int | None = None,
    limit: int = 50,
    tag: str | None = None,
    change_type: str | None = None,
    from_timestamp: str | None = None,
) -> dict[str, Any]:
    """List recent edits on the wiki.

    Args:
        namespace: Filter by namespace (default: all namespaces).
        limit: Maximum results (default: 50, max: 500).
        tag: Filter by tag name.
        change_type: Filter by type: edit, new, log, categorize, external.
        from_timestamp: Start from this timestamp (ISO 8601).

    Returns:
        List of recent changes with user, title, timestamp, and comment.
    """
    client = get_client()

    params: dict[str, Any] = {
        "list": "recentchanges",
        "rclimit": min(limit, 500),
        "rcprop": "user|title|timestamp|comment|sizes|ids|flags",
    }

    if namespace is not None:
        params["rcnamespace"] = namespace
    if tag:
        params["rctag"] = tag
    if change_type:
        params["rctype"] = change_type
    if from_timestamp:
        params["rcstart"] = from_timestamp

    return await client.query(params=params)
