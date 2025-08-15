from __future__ import annotations

import asyncio
from typing import Awaitable, Callable
from web3 import AsyncWeb3


async def poll_new_blocks(w3: AsyncWeb3, interval_sec: int, on_block: Callable[[int], Awaitable[None]]):
    last = await w3.eth.block_number
    while True:
        try:
            bn = await w3.eth.block_number
            if bn > last:
                for b in range(last + 1, bn + 1):
                    await on_block(b)
                last = bn
        except Exception:
            # best-effort; continue polling
            pass
        await asyncio.sleep(interval_sec)

