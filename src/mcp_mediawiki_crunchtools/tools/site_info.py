"""Site information tools.

Tools for getting wiki configuration and namespace information.
"""

from typing import Any

from ..client import get_client


async def get_site_info() -> dict[str, Any]:
    """Get wiki configuration and version info.

    Returns:
        Site info including wiki name, version, base URL, and features.
    """
    client = get_client()
    return await client.query(
        params={
            "meta": "siteinfo",
            "siprop": "general|statistics",
        },
    )


async def list_namespaces() -> dict[str, Any]:
    """List all namespaces on the wiki.

    Returns:
        List of namespaces with IDs, names, and canonical names.
    """
    client = get_client()
    return await client.query(
        params={
            "meta": "siteinfo",
            "siprop": "namespaces|namespacealiases",
        },
    )
