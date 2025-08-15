from __future__ import annotations

import asyncio
from typing import Any, Optional

import aiohttp
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

from .config import ScepticConfig


class HttpClient:
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def get(self, path: str, params: Optional[dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        async for attempt in AsyncRetrying(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=5)):
            with attempt:
                session = await self._get_session()
                async with session.get(url, params=params) as resp:
                    resp.raise_for_status()
                    return await resp.json()

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()


class CoingeckoClient(HttpClient):
    def __init__(self, base_url: str):
        super().__init__(base_url)

    async def simple_price(self, ids: list[str], vs_currencies: list[str] = ["usd"]) -> dict[str, Any]:
        ids_param = ",".join(ids)
        vs_param = ",".join(vs_currencies)
        return await self.get("simple/price", {"ids": ids_param, "vs_currencies": vs_param})


class DexscreenerClient(HttpClient):
    def __init__(self, base_url: str):
        super().__init__(base_url)

    async def search_pairs(self, query: str) -> dict[str, Any]:
        # https://api.dexscreener.com/latest/dex/search?q=<query>
        return await self.get("search", {"q": query})

    async def token_pairs(self, chain: str, token_address: str) -> dict[str, Any]:
        return await self.get(f"pairs/{chain}/{token_address}")


async def get_usd_price(cfg: ScepticConfig, coingecko_id: str) -> float:
    cg = CoingeckoClient(cfg.coingecko_base_url)
    data = await cg.simple_price([coingecko_id], ["usd"])
    await cg.close()
    return float(data.get(coingecko_id, {}).get("usd", 0.0))

