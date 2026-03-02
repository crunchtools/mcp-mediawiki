"""User information tools.

Tools for getting user details and contributions.
"""

from typing import Any

from ..client import get_client


async def get_user_info(
    username: str,
) -> dict[str, Any]:
    """Get user details.

    Args:
        username: Username to look up.

    Returns:
        User details including edit count, registration date, and groups.
    """
    if not username or not username.strip():
        raise ValueError("Username must not be empty")

    client = get_client()
    return await client.query(
        params={
            "list": "users",
            "ususers": username.strip(),
            "usprop": "editcount|registration|groups|blockinfo",
        },
    )


async def list_user_contributions(
    username: str,
    namespace: int | None = None,
    limit: int = 50,
    from_timestamp: str | None = None,
) -> dict[str, Any]:
    """List edits by a user.

    Args:
        username: Username whose contributions to list.
        namespace: Filter by namespace (default: all).
        limit: Maximum results (default: 50, max: 500).
        from_timestamp: Start from this timestamp (ISO 8601).

    Returns:
        List of user contributions with titles, timestamps, and comments.
    """
    if not username or not username.strip():
        raise ValueError("Username must not be empty")

    client = get_client()

    params: dict[str, Any] = {
        "list": "usercontribs",
        "ucuser": username.strip(),
        "uclimit": min(limit, 500),
        "ucprop": "title|timestamp|comment|sizediff|ids|flags",
    }

    if namespace is not None:
        params["ucnamespace"] = namespace
    if from_timestamp:
        params["ucstart"] = from_timestamp

    return await client.query(params=params)
