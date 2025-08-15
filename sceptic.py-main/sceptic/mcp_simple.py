from __future__ import annotations

import os
import time
from typing import Any

# Load .env file at startup
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from mcp.server.fastmcp import FastMCP, Context

# Simple MCP server without complex initialization
mcp = FastMCP(name="sceptic.py MCP Server")

@mcp.tool()
def health() -> dict:
    """Check server health"""
    return {"status": "ok", "message": "Server is running"}

@mcp.tool()
def echo(message: str) -> dict:
    """Echo a message"""
    return {"echo": message}

@mcp.tool()
def env_check() -> dict:
    """Check environment variables"""
    return {
        "chain_id": os.getenv("SCEPTIC_CHAIN_ID"),
        "write_tools": os.getenv("SCEPTIC_ENABLE_WRITE_TOOLS"),
        "private_key_set": bool(os.getenv("SCEPTIC_PRIVATE_KEY"))
    }

def main():
    mcp.run()

if __name__ == "__main__":
    main()
