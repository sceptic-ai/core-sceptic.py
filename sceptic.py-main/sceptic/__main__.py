from __future__ import annotations

import argparse
import asyncio
from .cli import _run_ws, _run_mcp


def main():
    parser = argparse.ArgumentParser(prog="python -m sceptic", description="Sceptic CLI")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("ws", help="Run WebSocket JSON-RPC server")
    sub.add_parser("mcp", help="Run MCP stdio JSON-RPC server")
    args = parser.parse_args()

    if args.cmd == "ws":
        asyncio.run(_run_ws())
    elif args.cmd == "mcp":
        _run_mcp()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

