import asyncio
import os

from sceptic import ScepticConfig
from sceptic.server import build_default_server


async def main():
    cfg = ScepticConfig.from_env()
    server = await build_default_server(cfg)
    print(f"Starting RPC server on ws://{cfg.server_host}:{cfg.server_port}")
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())

