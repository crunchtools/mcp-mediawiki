"""File/image information tools.

Tools for getting file metadata and listing files on the wiki.
"""

from typing import Any

from ..client import get_client
from ..models import validate_page_title


async def get_file_info(
    filename: str,
) -> dict[str, Any]:
    """Get file/image metadata.

    Args:
        filename: File name (with or without "File:" prefix).

    Returns:
        File metadata including URL, size, dimensions, and MIME type.
    """
    if not filename.startswith("File:"):
        filename = f"File:{filename}"
    validate_page_title(filename)

    client = get_client()
    return await client.query(
        params={
            "titles": filename,
            "prop": "imageinfo",
            "iiprop": "url|size|mime|timestamp|user|comment|sha1",
        },
    )


async def list_files(
    prefix: str | None = None,
    limit: int = 50,
    mime_type: str | None = None,
    from_name: str | None = None,
) -> dict[str, Any]:
    """List files on the wiki.

    Args:
        prefix: Filter files starting with this prefix.
        limit: Maximum results (default: 50, max: 500).
        mime_type: Filter by MIME type (e.g., "image/png").
        from_name: Start listing from this file (for pagination).

    Returns:
        List of files with metadata.
    """
    client = get_client()

    params: dict[str, Any] = {
        "list": "allimages",
        "ailimit": min(limit, 500),
        "aiprop": "url|size|mime|timestamp|user",
    }

    if prefix:
        params["aiprefix"] = prefix
    if mime_type:
        params["aimime"] = mime_type
    if from_name:
        params["aifrom"] = from_name

    return await client.query(params=params)
