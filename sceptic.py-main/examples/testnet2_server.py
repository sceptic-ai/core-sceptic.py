import asyncio
import os

from sceptic import ScepticConfig
from sceptic.server import build_default_server

# Quick-start for Core Testnet2 (chainId 1114)
# Required ENV:
#  SCEPTIC_RPC_HTTP_URL=https://rpc.test2.btcs.network
#  SCEPTIC_CHAIN_ID=1114
#  (optional) SCEPTIC_SERVER_API_TOKEN=...

async def main():
    cfg = ScepticConfig.from_env()
    server = await build_default_server(cfg)
    print(f"Starting RPC server on ws://{cfg.server_host}:{cfg.server_port} (chain {cfg.chain_id})")
    await server.start()

if __name__ == "__main__":
    asyncio.run(main())

