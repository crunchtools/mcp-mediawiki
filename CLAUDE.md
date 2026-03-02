# mcp-mediawiki-crunchtools

Secure MCP server for MediaWiki wikis. 19 tools across 7 categories.

## Quick Start

```bash
# Install and run
uvx mcp-mediawiki-crunchtools

# With Claude Code (read-only, public wiki)
claude mcp add mcp-mediawiki-crunchtools \
  --env MEDIAWIKI_URL=https://en.wikipedia.org/w/ \
  -- uvx mcp-mediawiki-crunchtools

# With authentication (for write operations)
claude mcp add mcp-mediawiki-crunchtools \
  --env MEDIAWIKI_URL=https://learn.fatherlinux.com/w/ \
  --env MEDIAWIKI_USERNAME=BotUser \
  --env MEDIAWIKI_PASSWORD=BotPassword \
  -- uvx mcp-mediawiki-crunchtools
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MEDIAWIKI_URL` | Yes | Wiki base URL (e.g., `https://en.wikipedia.org/w/`) |
| `MEDIAWIKI_USERNAME` | No | Bot/user account for write operations |
| `MEDIAWIKI_PASSWORD` | No | Bot/user password |
| `MEDIAWIKI_HTTP_USER` | No | HTTP Basic Auth username (.htaccess) |
| `MEDIAWIKI_HTTP_PASS` | No | HTTP Basic Auth password |

## Tools (19)

### Pages (8)
- `search` — Full-text search across wiki
- `get_page` — Get page wikitext content
- `get_page_html` — Parse page to HTML
- `list_pages` — List pages with prefix filter
- `create_page` — Create a new page (auth required)
- `edit_page` — Edit an existing page (auth required)
- `delete_page` — Delete a page (admin required)
- `move_page` — Move/rename a page (auth required)

### Categories (3)
- `list_categories` — List all categories
- `get_category_members` — Get pages in a category
- `get_page_categories` — Get categories for a page

### Recent Changes (1)
- `list_recent_changes` — List recent edits

### Parsing (1)
- `parse_wikitext` — Parse raw wikitext to HTML

### Site Info (2)
- `get_site_info` — Get wiki config and version
- `list_namespaces` — List wiki namespaces

### Users (2)
- `get_user_info` — Get user details
- `list_user_contributions` — List user edits

### Files (2)
- `get_file_info` — Get file/image metadata
- `list_files` — List files on the wiki

## Development

```bash
# Install dev dependencies
uv sync --all-extras

# Quality gates (run all five in order)
uv run ruff check src tests
uv run mypy src
uv run pytest -v
gourmand --full .
podman build -f Containerfile .
```

## Architecture

Two-layer tool pattern:
- `server.py` — `@mcp.tool()` wrappers (validation + delegation)
- `tools/*.py` — Pure async functions (API calls via `client.py`)

Authentication for writes uses MediaWiki clientlogin + CSRF tokens.
