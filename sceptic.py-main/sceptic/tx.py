from __future__ import annotations

import asyncio
from typing import Optional
from web3 import AsyncWeb3


async def wait_for_receipt(
    w3: AsyncWeb3,
    tx_hash: str,
    timeout_sec: int = 180,
    poll_interval_sec: float = 2.0,
) -> dict:
    deadline = asyncio.get_event_loop().time() + timeout_sec
    h = tx_hash if isinstance(tx_hash, (str, bytes)) else tx_hash.hex()
    while True:
        try:
            rec = await w3.eth.get_transaction_receipt(h)
            if rec:
                return rec
        except Exception:
            pass
        if asyncio.get_event_loop().time() > deadline:
            raise TimeoutError(f"Timeout waiting for receipt: {h}")
        await asyncio.sleep(poll_interval_sec)


async def ensure_confirmations(
    w3: AsyncWeb3, receipt: dict, confirmations: int = 1, poll_interval_sec: float = 2.0
) -> dict:
    tx_block = receipt.get("blockNumber")
    if tx_block is None:
        return receipt
    while True:
        bn = await w3.eth.block_number
        if bn - tx_block + 1 >= confirmations:
            return receipt
        await asyncio.sleep(poll_interval_sec)

