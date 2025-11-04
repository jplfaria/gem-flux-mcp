"""Main entry point for gem-flux-mcp package.

Allows running the server as:
    python -m gem_flux_mcp
    uv run python -m gem_flux_mcp
"""

from gem_flux_mcp.server import main

if __name__ == "__main__":
    main()
