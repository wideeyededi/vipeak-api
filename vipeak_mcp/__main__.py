"""Vipeak AI MCP server — entry point.

Run via `python -m vipeak_mcp` (stdio transport) or install the console script
`vipeak-mcp`. Configure with VIPEAK_BASE_URL and VIPEAK_API_KEY.
"""

from vipeak_mcp import main

if __name__ == "__main__":
    main()
