from __future__ import annotations

from web3 import AsyncWeb3


async def assert_chain_id(w3: AsyncWeb3, expected: int) -> None:
    cid = await w3.eth.chain_id
    if int(cid) != int(expected):
        raise ValueError(f"RPC chainId mismatch: expected {expected}, got {cid}")

