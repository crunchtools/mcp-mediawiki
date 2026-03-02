"""Pydantic models for input validation.

All tool inputs are validated through these models to prevent injection attacks
and ensure data integrity before making API calls.
"""

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

PAGE_TITLE_PATTERN = re.compile(r"^[^#<>\[\]{}|]+$")

MAX_TITLE_LENGTH = 255
MAX_CONTENT_LENGTH = 500_000
MAX_SUMMARY_LENGTH = 500
MAX_SEARCH_LENGTH = 300
MAX_PREFIX_LENGTH = 255


def validate_page_title(title: str) -> str:
    """Validate a MediaWiki page title.

    MediaWiki forbids: # < > [ ] { } |

    Args:
        title: Page title to validate.

    Returns:
        Validated title string.

    Raises:
        ValueError: If the title contains forbidden characters.
    """
    if not title or not title.strip():
        raise ValueError("Page title must not be empty")

    title = title.strip()

    if len(title) > MAX_TITLE_LENGTH:
        raise ValueError(f"Page title must not exceed {MAX_TITLE_LENGTH} characters")

    if not PAGE_TITLE_PATTERN.match(title):
        raise ValueError(
            "Page title contains forbidden characters (# < > [ ] { } |)"
        )

    return title


def validate_namespace_id(ns_id: int) -> int:
    """Validate a MediaWiki namespace ID.

    Args:
        ns_id: Namespace ID (0=Main, 1=Talk, 2=User, etc.).

    Returns:
        Validated namespace ID.

    Raises:
        ValueError: If namespace ID is out of valid range.
    """
    if ns_id < -2:
        raise ValueError("Namespace ID must be >= -2")
    return ns_id


class CreatePageInput(BaseModel):
    """Validated input for page creation."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(
        ..., min_length=1, max_length=MAX_TITLE_LENGTH, description="Page title"
    )
    content: str = Field(
        ..., min_length=1, max_length=MAX_CONTENT_LENGTH, description="Page wikitext content"
    )
    summary: str = Field(
        default="", max_length=MAX_SUMMARY_LENGTH, description="Edit summary"
    )

    @field_validator("title")
    @classmethod
    def check_title(cls, v: str) -> str:
        return validate_page_title(v)


class EditPageInput(BaseModel):
    """Validated input for page editing."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(
        ..., min_length=1, max_length=MAX_TITLE_LENGTH, description="Page title"
    )
    content: str = Field(
        ..., min_length=1, max_length=MAX_CONTENT_LENGTH, description="New page wikitext content"
    )
    summary: str = Field(
        default="", max_length=MAX_SUMMARY_LENGTH, description="Edit summary"
    )
    minor: bool = Field(
        default=False, description="Mark as minor edit"
    )

    @field_validator("title")
    @classmethod
    def check_title(cls, v: str) -> str:
        return validate_page_title(v)


class MovePageInput(BaseModel):
    """Validated input for page moving/renaming."""

    model_config = ConfigDict(extra="forbid")

    from_title: str = Field(
        ..., min_length=1, max_length=MAX_TITLE_LENGTH, description="Current page title"
    )
    to_title: str = Field(
        ..., min_length=1, max_length=MAX_TITLE_LENGTH, description="New page title"
    )
    reason: str = Field(
        default="", max_length=MAX_SUMMARY_LENGTH, description="Reason for move"
    )
    move_talk: bool = Field(
        default=True, description="Also move the talk page"
    )
    no_redirect: bool = Field(
        default=False, description="Do not create a redirect"
    )

    @field_validator("from_title", "to_title")
    @classmethod
    def check_title(cls, v: str) -> str:
        return validate_page_title(v)
