# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and this project adheres to
[Semantic Versioning](https://semver.org/).

Entries prior to 2026-09-19 are back-filled from GitHub Release notes (RT #1484).

## [Unreleased]

## [0.4.0] - 2026-11-08

### Added

- **The client says what it is.** Every request now carries
  `User-Agent: mcp-mediawiki-crunchtools/<version> (+<repo url>)`, with the
  version read from installed package metadata so it cannot drift from
  `pyproject.toml`. httpx's default is `python-httpx/<version>`, which
  Wikimedia's User-Agent policy refuses outright and which Cloudflare's bot
  protection answers with an HTML challenge page instead of the API — the
  failure that cost an afternoon on mcp-wordpress (RT #1596). This server was
  one policy change away from the same outage.

### Fixed

- **The response ceiling is now a ceiling.** It read the `content-length`
  header and nothing else, and that header is optional: a chunked reply carried
  none and was read without limit. The body is now read in bounded pieces and
  the read aborts the moment the running total passes `MAX_RESPONSE_SIZE`. The
  header is still an early reject, now guarded so a malformed value is not an
  unhandled `ValueError`.

- **An error says which site answered, and with what.** Failures reported
  `HTTP 403` and nothing else, so a WAF challenge, a login redirect and a
  genuine API error were one message. They now name the method, the full
  requested URL, the status, the content-type and a short body snippet — the
  full URL and not the configured one, because an `http` base that 301s to
  `https` returns an HTML body and reproduces this module's JSON error byte for
  byte.

- **`_login` checked nothing at all.** Its two calls went straight to `.json()`
  on an unread body, so a challenge page there surfaced as a bare
  `JSONDecodeError`. Every request in the module now goes through one
  `_request`, which is what makes that impossible rather than merely fixed.

### Changed

- Client tests drive a real `httpx.AsyncClient` over `httpx.MockTransport`
  instead of an `AsyncMock` standing in for the client. The client is what sets
  the agent string and what reads the body in pieces, so mocking its methods
  mocked away the behaviour the tests are now there to hold.

- Inherits constitution v1.36.0, whose MCP Server profile 1.8.0 states this
  contract and checks it.

## [0.3.0] - 2026-11-03

### Added

- `MEDIAWIKI_ALLOW_HTTP=true` permits a plain `http://` `MEDIAWIKI_URL` for a
  wiki reached over a private container network, where there is no TLS
  endpoint. Off by default, and the host must be a private IP literal;
  HTTPS is still required otherwise (RT #1546).

## [0.2.2] - 2026-10-31

### Security

- Upgraded locked dependencies within their declared ranges to clear the
  advisories the fleet dependency audit found (anyio, authlib, certifi, cryptography, dnspython, fastmcp, joserfc, opentelemetry-api, pydantic-settings, pygments, pyjwt).

## [0.2.1] - 2026-10-20

### Fixed

- `search_tool` returned no results on MediaWiki 1.43 with the MySQL search
  backend. It now asks for a full-text search (`srwhat=text`).

### Changed

- Container base images pinned to `quay.io/hummingbird/python:3.14*` instead of
  `latest`, which moved to Python 3.15.0 on 2026-10-20 (crunchtools/constitution#66).

## [0.2.0] - 2026-10-10

### Added

- The fifteen tools that only read publish `readOnlyHint: true`: every tool
  except `create_page`, `edit_page`, `delete_page` and `move_page`. A gateway
  uses it to decide whether an invalid optional argument may be dropped or must
  refuse the call (crunchtools/constitution#35).
- Tests pin every registered tool into `READ_ONLY` or `WRITES`, and check that
  a read-only tool sends the wiki only `action=query` or `action=parse` (plus
  the `action=login` handshake) and never asks for a CSRF token.

### Fixed

- The Containerfile `version` label said 0.1.3 through the 0.1.4 release; it
  carries the release version again.

### Changed

- Inherits constitution v1.22.0; the workflow pins and the pre-commit hook rev
  move with it.
- Constitution is now a v1.18.0 manifest: it holds only what is specific to
  this repo; fleet and profile rules apply by reference.
- Constitution validation is pinned to the inherited release via
  `.github/workflows/constitution.yml`.
- Dependabot auto-merges GitHub Actions minor and patch updates.

## [0.1.4] - 2026-09-20

### Fixed

- v0.1.3's container build never reached GHCR. The single combined
  `build-and-push` job pinned `aquasecurity/trivy-action@0.34.1`, which
  Aquasecurity has since deleted from the Marketplace, so the job now fails
  during action resolution before any push step runs, and the historical
  workflow can no longer be replayed to backfill the missing GHCR image.
  CI has since migrated to the two-job `build-and-push-quay` /
  `build-and-push-ghcr` architecture (Constitution Section III) with a
  current Trivy pin, so cutting v0.1.4 is what actually lands the release in
  both registries.

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
