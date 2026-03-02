# Security Design Document

This document describes the security architecture of mcp-mediawiki-crunchtools.

## 1. Threat Model

### 1.1 Assets to Protect

| Asset | Sensitivity | Impact if Compromised |
|-------|-------------|----------------------|
| MediaWiki Password | Critical | Full wiki account access, content manipulation |
| HTTP Basic Auth Credentials | Critical | Bypass .htaccess protection |
| Wiki Content | Medium | Information disclosure, content vandalism |
| Session Cookies | High | Session hijacking, unauthorized edits |

### 1.2 Threat Actors

| Actor | Capability | Motivation |
|-------|------------|------------|
| Malicious AI Agent | Can craft tool inputs | Data exfiltration, content vandalism |
| Local Attacker | Access to filesystem | Credential theft, configuration tampering |
| Network Attacker | Man-in-the-middle | Credential interception (mitigated by TLS) |

### 1.3 Attack Vectors

| Vector | Description | Mitigation |
|--------|-------------|------------|
| Credential Leakage | Password exposed in logs, errors, or outputs | Never log passwords, scrub from errors |
| Input Injection | Malicious page titles or content | Strict input validation with Pydantic |
| CSRF Bypass | Forged write requests | CSRF token required for all write operations |
| SSRF | Redirect API calls to internal services | HTTPS enforcement, URL validation |
| Session Hijacking | Stolen session cookies | Cookie persistence in httpx client only |

## 2. Security Architecture

### 2.1 Defense in Depth Layers

```
Layer 1: Input Validation
  - Pydantic models for all tool inputs
  - Forbidden character validation for page titles
  - Reject unexpected fields (extra="forbid")

Layer 2: Credential Handling
  - Environment variable only (never file, never arg)
  - Never log, never include in errors
  - Passwords stored as SecretStr

Layer 3: API Client Hardening
  - HTTPS enforcement for non-localhost URLs
  - TLS certificate validation (httpx default)
  - Request timeout enforcement (30s)
  - Response size limits (10MB)

Layer 4: Output Sanitization
  - Redact passwords from any error messages
  - Limit response sizes to prevent memory exhaustion
  - Structured errors without internal details

Layer 5: Runtime Protection
  - No filesystem access
  - No shell execution (subprocess)
  - No dynamic code evaluation (eval/exec)
  - Type-safe with Pydantic

Layer 6: Supply Chain Security
  - Automated CVE scanning via GitHub Actions
  - Container built on Hummingbird for minimal CVEs
  - Gourmand AI slop detection gating all PRs
```

### 2.2 Authentication Flow

Write operations use MediaWiki's clientlogin flow:

1. Fetch login token via `action=query&meta=tokens&type=login`
2. Authenticate via `action=clientlogin` with username + password + token
3. Session cookies stored in persistent httpx client (memory only)
4. Before each write: fetch CSRF token via `action=query&meta=tokens&type=csrf`
5. CSRF token included in edit/delete/move POST requests
6. On badtoken error: refresh CSRF token and retry once

### 2.3 URL Security

The wiki URL is validated to prevent SSRF:

- Must be a valid URL with scheme and netloc
- Must use HTTPS unless connecting to localhost
- Trailing slashes are stripped
- API URL derived as `{MEDIAWIKI_URL}/api.php`

## 3. Minimum Permission Levels

### 3.1 Read-Only (No Auth)

No credentials needed. Works with any public wiki.

Capabilities: search, get_page, list_pages, categories, site info, users, files

### 3.2 Authenticated User

Set `MEDIAWIKI_USERNAME` and `MEDIAWIKI_PASSWORD`.

Capabilities: All read tools + create_page, edit_page, move_page

### 3.3 Admin User

Admin account credentials required.

Capabilities: All tools including delete_page

## 4. Reporting Security Issues

Report security vulnerabilities using GitHub's private security advisory at
https://github.com/crunchtools/mcp-mediawiki/security/advisories/new

Do NOT open public issues for security vulnerabilities.
