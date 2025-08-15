from __future__ import annotations

import asyncio
from typing import Dict
from web3 import AsyncWeb3


class NonceManager:
    def __init__(self, w3: AsyncWeb3):
        self.w3 = w3
        self._locks: Dict[str, asyncio.Lock] = {}
        self._nonces: Dict[str, int] = {}

    def _key(self, addr: str) -> str:
        return self.w3.to_checksum_address(addr)

    async def get_next(self, address: str) -> int:
        k = self._key(address)
        lock = self._locks.setdefault(k, asyncio.Lock())
        async with lock:
            if k not in self._nonces:
                self._nonces[k] = await self.w3.eth.get_transaction_count(k)
            n = self._nonces[k]
            self._nonces[k] = n + 1
            return n

    async def reset(self, address: str) -> None:
        k = self._key(address)
        self._nonces.pop(k, None)

