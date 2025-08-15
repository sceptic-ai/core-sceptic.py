from __future__ import annotations

import asyncio
import os
from sceptic import ScepticConfig
from sceptic.server import build_default_server


def run_ws():
    asyncio.run(_run_ws())


def run_mcp():
    _run_mcp()


async def _run_ws():
    cfg = ScepticConfig.from_env()
    if not cfg.rpc_http_url:
        print("Error: SCEPTIC_RPC_HTTP_URL is empty. Set it or SCEPTIC_CHAIN_ID=1114 for auto-fill.")
        raise SystemExit(2)
    server = await build_default_server(cfg)
    print(f"Starting RPC server on ws://{cfg.server_host}:{cfg.server_port} (chain {cfg.chain_id})")
    try:
        await server.start()
    except KeyboardInterrupt:
        print("Shutting down WS server...")


def _run_mcp():
    print("Starting MCP stdio (FastMCP)")
    try:
        # Lazy import to avoid requiring modelcontextprotocol unless MCP is used
        from sceptic.mcp_server import mcp  # type: ignore
    except Exception as e:
        print("Error: Failed to import MCP server. Ensure 'modelcontextprotocol' is installed (pip install modelcontextprotocol).")
        raise
    try:
        mcp.run()
    except KeyboardInterrupt:
        print("Shutting down MCP stdio server...")

