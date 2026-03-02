"""Tests for Pydantic model validation.

These tests verify that input validation models correctly accept valid inputs
and reject invalid inputs.
"""

import pytest
from pydantic import ValidationError

from mcp_mediawiki_crunchtools.models import (
    CreatePageInput,
    EditPageInput,
    MovePageInput,
    validate_namespace_id,
    validate_page_title,
)


class TestPageTitleValidation:
    """Tests for page title validation."""

    def test_valid_title(self) -> None:
        """Valid titles should pass."""
        assert validate_page_title("Main Page") == "Main Page"
        assert validate_page_title("User:Admin") == "User:Admin"
        assert validate_page_title("Category:Test") == "Category:Test"

    def test_title_strips_whitespace(self) -> None:
        """Titles should be stripped of leading/trailing whitespace."""
        assert validate_page_title("  Test Page  ") == "Test Page"

    def test_empty_title_rejected(self) -> None:
        """Empty titles should be rejected."""
        with pytest.raises(ValueError, match="must not be empty"):
            validate_page_title("")

    def test_whitespace_only_title_rejected(self) -> None:
        """Whitespace-only titles should be rejected."""
        with pytest.raises(ValueError, match="must not be empty"):
            validate_page_title("   ")

    def test_long_title_rejected(self) -> None:
        """Titles exceeding max length should be rejected."""
        with pytest.raises(ValueError, match="must not exceed"):
            validate_page_title("x" * 256)

    def test_forbidden_chars_rejected(self) -> None:
        """Titles with forbidden characters should be rejected."""
        forbidden_chars = ["#", "<", ">", "[", "]", "{", "}", "|"]
        for char in forbidden_chars:
            with pytest.raises(ValueError, match="forbidden characters"):
                validate_page_title(f"Test{char}Page")


class TestNamespaceIdValidation:
    """Tests for namespace ID validation."""

    def test_valid_namespace_ids(self) -> None:
        """Valid namespace IDs should pass."""
        assert validate_namespace_id(0) == 0
        assert validate_namespace_id(1) == 1
        assert validate_namespace_id(-2) == -2
        assert validate_namespace_id(100) == 100

    def test_invalid_namespace_id(self) -> None:
        """Namespace IDs below -2 should be rejected."""
        with pytest.raises(ValueError, match="must be >= -2"):
            validate_namespace_id(-3)


class TestCreatePageInput:
    """Tests for CreatePageInput model."""

    def test_valid_minimal(self) -> None:
        """Minimal valid input should pass."""
        inp = CreatePageInput(title="Test", content="Hello")
        assert inp.title == "Test"
        assert inp.content == "Hello"
        assert inp.summary == ""

    def test_valid_full(self) -> None:
        """Full valid input should pass."""
        inp = CreatePageInput(
            title="Test Page", content="Content here", summary="Created page",
        )
        assert inp.title == "Test Page"
        assert inp.summary == "Created page"

    def test_empty_title_rejected(self) -> None:
        """Empty title should be rejected."""
        with pytest.raises(ValidationError):
            CreatePageInput(title="", content="Hello")

    def test_empty_content_rejected(self) -> None:
        """Empty content should be rejected."""
        with pytest.raises(ValidationError):
            CreatePageInput(title="Test", content="")

    def test_forbidden_chars_in_title_rejected(self) -> None:
        """Title with forbidden chars should be rejected."""
        with pytest.raises(ValidationError):
            CreatePageInput(title="Test[Page]", content="Hello")

    def test_extra_fields_rejected(self) -> None:
        """Extra fields should be rejected (Pydantic extra=forbid)."""
        with pytest.raises(ValidationError):
            CreatePageInput(
                title="Test",
                content="Hello",
                evil_field="injection",  # type: ignore[call-arg]
            )


class TestEditPageInput:
    """Tests for EditPageInput model."""

    def test_valid_edit(self) -> None:
        """Valid edit input should pass."""
        inp = EditPageInput(
            title="Test", content="Updated", summary="Fixed typo", minor=True,
        )
        assert inp.title == "Test"
        assert inp.minor is True

    def test_defaults(self) -> None:
        """Defaults should be applied."""
        inp = EditPageInput(title="Test", content="Updated")
        assert inp.summary == ""
        assert inp.minor is False


class TestMovePageInput:
    """Tests for MovePageInput model."""

    def test_valid_move(self) -> None:
        """Valid move input should pass."""
        inp = MovePageInput(
            from_title="Old Name", to_title="New Name", reason="Renaming",
        )
        assert inp.from_title == "Old Name"
        assert inp.to_title == "New Name"
        assert inp.move_talk is True
        assert inp.no_redirect is False

    def test_forbidden_chars_in_from_title(self) -> None:
        """Forbidden chars in from_title should be rejected."""
        with pytest.raises(ValidationError):
            MovePageInput(from_title="Test[Bad]", to_title="Good Title")

    def test_forbidden_chars_in_to_title(self) -> None:
        """Forbidden chars in to_title should be rejected."""
        with pytest.raises(ValidationError):
            MovePageInput(from_title="Good Title", to_title="Test{Bad}")
