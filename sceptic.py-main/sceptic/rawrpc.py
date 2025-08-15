from __future__ import annotations

import json
from typing import Any, Optional
import aiohttp
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential


class RawRpc:
    def __init__(self, url: str, timeout: int = 30):
        self.url = url
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None

    async def _session_get(self) -> aiohttp.ClientSession:
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        return self._session

    async def call(self, method: str, params: list[Any] | None = None, id: int = 1) -> Any:
        payload = {"jsonrpc": "2.0", "method": method, "params": params or [], "id": id}
        async for attempt in AsyncRetrying(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=5)):
            with attempt:
                s = await self._session_get()
                async with s.post(self.url, json=payload) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    if "error" in data:
                        raise RuntimeError(data["error"]) 
                    return data.get("result")

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

