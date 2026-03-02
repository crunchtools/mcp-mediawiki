# mcp-mediawiki-crunchtools

Secure MCP server for MediaWiki wikis. Search, read, create, edit, and manage wiki pages, categories, files, and more. Works with any MediaWiki instance — public or private.

## Installation

### uvx (recommended)

```bash
uvx mcp-mediawiki-crunchtools
```

### pip

```bash
pip install mcp-mediawiki-crunchtools
mcp-mediawiki-crunchtools
```

### Container

```bash
podman run -e MEDIAWIKI_URL=https://en.wikipedia.org/w/ \
  quay.io/crunchtools/mcp-mediawiki
```

## Usage with Claude Code

### Read-only (public wiki, no auth needed)

```bash
claude mcp add mcp-mediawiki-crunchtools \
  --env MEDIAWIKI_URL=https://en.wikipedia.org/w/ \
  -- uvx mcp-mediawiki-crunchtools
```

### With authentication (for write operations)

```bash
claude mcp add mcp-mediawiki-crunchtools \
  --env MEDIAWIKI_URL=https://your-wiki.com/w/ \
  --env MEDIAWIKI_USERNAME=BotUser \
  --env MEDIAWIKI_PASSWORD=BotPassword \
  -- uvx mcp-mediawiki-crunchtools
```

### HTTP transport (systemd / container)

```bash
podman run -d --name mcp-mediawiki \
  -p 127.0.0.1:8016:8016 \
  -e MEDIAWIKI_URL=https://your-wiki.com/w/ \
  quay.io/crunchtools/mcp-mediawiki \
  --transport streamable-http --host 0.0.0.0
```

Claude Code config:
```json
{"type": "http", "url": "http://127.0.0.1:8016/mcp"}
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

| Category | Tool | Description |
|----------|------|-------------|
| Pages | `search` | Full-text search across wiki |
| Pages | `get_page` | Get page wikitext content |
| Pages | `get_page_html` | Parse page to HTML |
| Pages | `list_pages` | List pages with prefix filter |
| Pages | `create_page` | Create a new page |
| Pages | `edit_page` | Edit an existing page |
| Pages | `delete_page` | Delete a page |
| Pages | `move_page` | Move/rename a page |
| Categories | `list_categories` | List all categories |
| Categories | `get_category_members` | Get pages in a category |
| Categories | `get_page_categories` | Get categories for a page |
| Recent Changes | `list_recent_changes` | List recent edits |
| Parsing | `parse_wikitext` | Parse raw wikitext to HTML |
| Site Info | `get_site_info` | Get wiki config and version |
| Site Info | `list_namespaces` | List wiki namespaces |
| Users | `get_user_info` | Get user details |
| Users | `list_user_contributions` | List user edits |
| Files | `get_file_info` | Get file/image metadata |
| Files | `list_files` | List files on the wiki |

## Development

```bash
# Install dev dependencies
uv sync --all-extras

# Quality gates
uv run ruff check src tests
uv run mypy src
uv run pytest -v
gourmand --full .
podman build -f Containerfile .
```

## License

AGPL-3.0-or-later

<!-- mcp-name: io.github.crunchtools/mediawiki -->
