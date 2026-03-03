# MCP MediaWiki CrunchTools Container
# Built on Hummingbird Python image (Red Hat UBI-based) for enterprise security
#
# Build:
#   podman build -t quay.io/crunchtools/mcp-mediawiki .
#
# Run:
#   podman run -e MEDIAWIKI_URL=https://en.wikipedia.org/w/ \
#     quay.io/crunchtools/mcp-mediawiki
#
# With Claude Code:
#   claude mcp add mcp-mediawiki-crunchtools \
#     --env MEDIAWIKI_URL=https://en.wikipedia.org/w/ \
#     -- podman run -i --rm -e MEDIAWIKI_URL quay.io/crunchtools/mcp-mediawiki

# Use Hummingbird Python image (Red Hat UBI-based with Python pre-installed)
FROM quay.io/hummingbird/python:latest

# Labels for container metadata
LABEL name="mcp-mediawiki-crunchtools" \
      version="0.1.3" \
      summary="Secure MCP server for MediaWiki wikis" \
      description="A security-focused MCP server for MediaWiki built on Red Hat UBI" \
      maintainer="crunchtools.com" \
      url="https://github.com/crunchtools/mcp-mediawiki" \
      io.k8s.display-name="MCP MediaWiki CrunchTools" \
      io.openshift.tags="mcp,mediawiki,wiki" \
      org.opencontainers.image.source="https://github.com/crunchtools/mcp-mediawiki" \
      org.opencontainers.image.description="Secure MCP server for MediaWiki wikis" \
      org.opencontainers.image.licenses="AGPL-3.0-or-later"

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install the package and dependencies
RUN pip install --no-cache-dir .

# Verify installation
RUN python -c "from mcp_mediawiki_crunchtools import main; print('Installation verified')"

# Default: stdio transport (use -i with podman run)
# HTTP:    --transport streamable-http (use -d -p 8016:8016 with podman run)
EXPOSE 8016
ENTRYPOINT ["python", "-m", "mcp_mediawiki_crunchtools"]
