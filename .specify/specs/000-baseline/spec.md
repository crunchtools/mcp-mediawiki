# Spec 000: Baseline

> **Status:** Complete
> **Created:** 2026-03-01

## Overview

Initial baseline specification for mcp-mediawiki-crunchtools v0.1.0.

## Tool Inventory (19 tools, 7 categories)

### Pages (8 tools)
| Tool | Action API | Auth |
|------|-----------|------|
| `search` | `action=query&list=search` | No |
| `get_page` | `action=query&prop=revisions` | No |
| `get_page_html` | `action=parse&page=` | No |
| `list_pages` | `action=query&list=allpages` | No |
| `create_page` | `action=edit` (createonly) | Yes |
| `edit_page` | `action=edit` | Yes |
| `delete_page` | `action=delete` | Yes (admin) |
| `move_page` | `action=move` | Yes |

### Categories (3 tools)
| Tool | Action API | Auth |
|------|-----------|------|
| `list_categories` | `action=query&list=allcategories` | No |
| `get_category_members` | `action=query&list=categorymembers` | No |
| `get_page_categories` | `action=query&prop=categories` | No |

### Recent Changes (1 tool)
| Tool | Action API | Auth |
|------|-----------|------|
| `list_recent_changes` | `action=query&list=recentchanges` | No |

### Parsing (1 tool)
| Tool | Action API | Auth |
|------|-----------|------|
| `parse_wikitext` | `action=parse&text=` | No |

### Site Info (2 tools)
| Tool | Action API | Auth |
|------|-----------|------|
| `get_site_info` | `action=query&meta=siteinfo` | No |
| `list_namespaces` | `action=query&meta=siteinfo&siprop=namespaces` | No |

### Users (2 tools)
| Tool | Action API | Auth |
|------|-----------|------|
| `get_user_info` | `action=query&list=users` | No |
| `list_user_contributions` | `action=query&list=usercontribs` | No |

### Files (2 tools)
| Tool | Action API | Auth |
|------|-----------|------|
| `get_file_info` | `action=query&prop=imageinfo` | No |
| `list_files` | `action=query&list=allimages` | No |

## Module Structure

```
src/mcp_mediawiki_crunchtools/
  __init__.py          # Entry point, argparse, version
  __main__.py          # python -m support
  server.py            # FastMCP server + @mcp.tool() wrappers
  client.py            # MediaWiki API client (httpx, auth, CSRF)
  config.py            # Config with SecretStr, URL validation
  errors.py            # UserError hierarchy
  models.py            # Pydantic input validation
  tools/
    __init__.py        # Re-exports all 19 functions
    pages.py           # 8 tools
    categories.py      # 3 tools
    recent_changes.py  # 1 tool
    parsing.py         # 1 tool
    site_info.py       # 2 tools
    users.py           # 2 tools
    files.py           # 2 tools
```

## Security Architecture

See SECURITY.md for full threat model and defense-in-depth layers.
