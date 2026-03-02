# mcp-mediawiki-crunchtools Constitution

> **Version:** 1.0.0
> **Ratified:** 2026-03-01
> **Status:** Active

This constitution establishes the core principles, constraints, and workflows that govern all development on mcp-mediawiki-crunchtools.

---

## I. Core Principles

### 1. Five-Layer Security Model

Every change MUST preserve all five security layers. No exceptions.

**Layer 1 — Credential Protection:**
- Passwords stored as `SecretStr` (never logged or exposed)
- Environment-variable-only storage
- Automatic scrubbing from error messages

**Layer 2 — Input Validation:**
- Pydantic models enforce strict data types with `extra="forbid"`
- Forbidden character validation for page titles
- Content length limits enforced

**Layer 3 — API Hardening:**
- CSRF tokens required for all write operations
- Mandatory TLS certificate validation
- Request timeouts and response size limits
- HTTPS enforcement for non-localhost URLs

**Layer 4 — Dangerous Operation Prevention:**
- No filesystem access, shell execution, or code evaluation
- No `eval()`/`exec()` functions
- Tools are pure API wrappers with no side effects

**Layer 5 — Supply Chain Security:**
- Weekly automated CVE scanning via GitHub Actions
- Hummingbird container base images (minimal CVE surface)
- Gourmand AI slop detection gating all PRs

### 2. Two-Layer Tool Architecture

Tools follow a strict two-layer pattern:
- `server.py` — `@mcp.tool()` decorated functions that validate args and delegate
- `tools/*.py` — Pure async functions that call `client.py` HTTP methods

Never put business logic in `server.py`. Never put MCP registration in `tools/*.py`.

### 3. Any-Instance Compatibility

The server MUST work with any MediaWiki instance:
- Public wikis (Wikipedia, Fedora Wiki) work without auth
- Private wikis use clientlogin authentication
- `.htaccess`-protected wikis use HTTP Basic Auth
- HTTPS enforced for non-localhost URLs

### 4. Three Distribution Channels

Every release MUST be available through all three channels:

| Channel | Command | Use Case |
|---------|---------|----------|
| uvx | `uvx mcp-mediawiki-crunchtools` | Zero-install, Claude Code |
| pip | `pip install mcp-mediawiki-crunchtools` | Virtual environments |
| Container | `podman run quay.io/crunchtools/mcp-mediawiki` | Isolated, systemd |

### 5. Semantic Versioning

Follow Semantic Versioning 2.0.0 strictly.

---

## II. Technology Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Language | Python | 3.10+ |
| MCP Framework | FastMCP | Latest |
| HTTP Client | httpx | Latest |
| Validation | Pydantic | v2 |
| Container Base | Hummingbird | Latest |
| Package Manager | uv | Latest |
| Build System | hatchling | Latest |
| Linter | ruff | Latest |
| Type Checker | mypy (strict) | Latest |
| Tests | pytest + pytest-asyncio | Latest |
| Slop Detector | gourmand | Latest |

---

## III. Testing Standards

### Mocked API Tests (MANDATORY)

Every tool MUST have a corresponding mocked test. Tests use `httpx.AsyncClient` mocking.

**Pattern:**
1. Build a mock `httpx.Response` with `_mock_response()` helper
2. Patch `httpx.AsyncClient` via `_patch_client()` context manager
3. Call the tool function directly (not the `_tool` wrapper)
4. Assert response structure and values

**Tool count assertion:** `test_tool_count` MUST be updated whenever tools are added or removed.

---

## IV. Code Quality Gates

Every code change must pass through these gates in order:

1. **Lint** — `uv run ruff check src tests`
2. **Type Check** — `uv run mypy src`
3. **Tests** — `uv run pytest -v`
4. **Gourmand** — `gourmand --full .`
5. **Container Build** — `podman build -f Containerfile .`

---

## V. Naming Conventions

| Context | Name |
|---------|------|
| GitHub repo | `crunchtools/mcp-mediawiki` |
| PyPI package | `mcp-mediawiki-crunchtools` |
| CLI command | `mcp-mediawiki-crunchtools` |
| Python module | `mcp_mediawiki_crunchtools` |
| Container image | `quay.io/crunchtools/mcp-mediawiki` |
| systemd service | `mcp-mediawiki.service` |
| HTTP port | 8016 |
| License | AGPL-3.0-or-later |

---

## VI. Development Workflow

### Adding a New Tool

1. Add the async function to the appropriate `tools/*.py` file
2. Export it from `tools/__init__.py`
3. Import it in `server.py` and register with `@mcp.tool()`
4. Add a mocked test in `tests/test_tools.py`
5. Update the tool count in `test_tool_count`
6. Run all five quality gates
7. Update CLAUDE.md tool listing

---

## VII. Governance

### Ratification History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-01 | Initial constitution |
