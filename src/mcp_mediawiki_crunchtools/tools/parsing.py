"""Parsing tools.

Tools for parsing raw wikitext to HTML.
"""

from typing import Any

from ..client import get_client


async def parse_wikitext(
    wikitext: str,
    title: str | None = None,
) -> dict[str, Any]:
    """Parse raw wikitext to HTML.

    Args:
        wikitext: Raw wikitext content to parse.
        title: Context page title for template resolution (optional).

    Returns:
        Parsed HTML output.
    """
    if not wikitext or not wikitext.strip():
        raise ValueError("Wikitext must not be empty")

    client = get_client()

    params: dict[str, Any] = {
        "text": wikitext,
        "contentmodel": "wikitext",
        "prop": "text",
    }

    if title:
        params["title"] = title

    return await client.parse(params=params)
