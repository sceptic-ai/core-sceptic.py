import asyncio
import os

from sceptic import ScepticConfig
from sceptic.mcp_stdio import build_mcp_server


async def main():
    cfg = ScepticConfig.from_env()
    server = await build_mcp_server(cfg)
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())

