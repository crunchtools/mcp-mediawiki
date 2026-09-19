# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and this project adheres to
[Semantic Versioning](https://semver.org/).

Entries prior to 2026-09-19 are back-filled from GitHub Release notes (RT #1484).

## [Unreleased]

## [0.1.3] - 2026-03-02

Patch release with bug fixes and dependency updates.

### Changed
- Dependency updates.
- Code quality improvements.

## [0.1.1] - 2026-03-01

No GitHub Release was created for this tag, so no authored release notes exist to
back-fill from. There is no `v0.1.2` tag.

## [0.1.0] - 2026-03-01

Initial release. Secure MCP server for MediaWiki wikis with 19 tools across 7
categories.

### Added
- Pages (8): `search`, `get_page`, `get_page_html`, `list_pages`, `create_page`,
  `edit_page`, `delete_page`, `move_page`.
- Categories (3): `list_categories`, `get_category_members`, `get_page_categories`.
- Recent Changes (1): `list_recent_changes`.
- Parsing (1): `parse_wikitext`.
- Site Info (2): `get_site_info`, `list_namespaces`.
- Users (2): `get_user_info`, `list_user_contributions`.
- Files (2): `get_file_info`, `list_files`.
- 54 mocked tests (pytest), strict mypy type checking, zero gourmand violations,
  Hummingbird container base, full CI/CD pipeline.
