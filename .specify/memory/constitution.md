# mcp-mediawiki-crunchtools Constitution

> **Version:** 1.1.0
> **Ratified:** 2026-03-01
> **Amended:** 2026-10-02
> **Status:** Active
> **Inherits:** [crunchtools/constitution](https://github.com/crunchtools/constitution) v1.20.0
> **Profile:** MCP Server

This file holds what is specific to mcp-mediawiki. The fleet rules and the
MCP Server profile (five-layer security model, two-layer tools, distribution
channels, transports, quality gates, Gourmand) apply at the inherited version
and are checked against this repo's files by `constitution.yml`. They are not
restated here.

## Security Model Specifics

- **Credentials:** all optional. `MEDIAWIKI_USERNAME` with
  `MEDIAWIKI_PASSWORD` for clientlogin, and `MEDIAWIKI_HTTP_USER` with
  `MEDIAWIKI_HTTP_PASS` for HTTP Basic Auth; each password is required when
  its user is set. Passwords are held as `SecretStr`, read from the
  environment only and scrubbed from error messages.
- **Input limits:** Pydantic models with `extra="forbid"`; page titles
  reject MediaWiki's forbidden characters (`# < > [ ] { } |`) and are capped
  at 255 characters, content at 500,000, edit summaries at 500, search
  strings at 300, prefixes at 255.
- **API:** every write fetches a CSRF token first; requests time out after
  30s; responses are capped at 10MB.
- **Surface:** pure API wrappers against `api.php`. No filesystem access,
  shell execution or code evaluation.

## Any-Instance Compatibility

The server works with any MediaWiki instance. `MEDIAWIKI_URL` (required) is
the wiki base, and must be HTTPS unless the host is localhost. Public wikis
work without auth, private wikis use clientlogin, and `.htaccess`-protected
wikis use HTTP Basic Auth.

## Instance

| Context | Name |
|---------|------|
| GitHub repo | `crunchtools/mcp-mediawiki` |
| PyPI package | `mcp-mediawiki-crunchtools` |
| Container image | `quay.io/crunchtools/mcp-mediawiki` |
| systemd service | `mcp-mediawiki.service` |
| HTTP port | 8016 |

## History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-01 | Initial constitution |
| 1.0.1 | 2026-03-16 | Add Section VI (Container Conventions); renumber VI-VIII to VII-IX |
| 1.0.2 | 2026-09-25 | Inherit constitution v1.17.0 (Gatehouse gates) |
| 1.1.0 | 2026-10-02 | Manifest under constitution v1.18.0: profile restatement removed, mcp-mediawiki specifics kept |
