#!/usr/bin/env python3

import sys
import json
from mcp.server.fastmcp import FastMCP

# Simple test MCP server
mcp = FastMCP(name="Test MCP Server")

@mcp.tool()
def hello(name: str = "World") -> str:
    """Say hello to someone"""
    return f"Hello, {name}!"

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

if __name__ == "__main__":
    print("Starting test MCP server...", file=sys.stderr)
    try:
        mcp.run()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
