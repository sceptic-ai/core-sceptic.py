from __future__ import annotations

import asyncio
from typing import Optional
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential
from web3 import AsyncWeb3
from web3.eth import AsyncEth

# Web3 v7+ exposes AsyncHTTPProvider at top-level; v6 uses web3.providers.async_rpc
try:  # pragma: no cover - import compatibility shim
    from web3 import AsyncHTTPProvider  # type: ignore
except Exception:  # pragma: no cover
    from web3.providers.async_rpc import AsyncHTTPProvider  # type: ignore

# geth_poa_middleware import compatibility (async variant may not exist)
try:  # pragma: no cover
    from web3.middleware import geth_poa_middleware  # type: ignore
except Exception:  # pragma: no cover
    try:
        from web3.middleware.proof_of_authority import geth_poa_middleware  # type: ignore
    except Exception:
        geth_poa_middleware = None  # type: ignore

from .config import ScepticConfig


async def _probe_provider(w3: AsyncWeb3, timeout: int) -> None:
    # Python 3.10-compatible timeout handling
    await asyncio.wait_for(w3.eth.block_number, timeout=timeout)


def get_async_web3(cfg: ScepticConfig) -> AsyncWeb3:
    w3 = AsyncWeb3(AsyncHTTPProvider(cfg.rpc_http_url, request_kwargs={"timeout": cfg.request_timeout_sec}))
    if geth_poa_middleware is not None:
        try:
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        except Exception:
            pass
    w3.eth = AsyncEth(w3)  # type: ignore[attr-defined]
    return w3


async def ensure_web3_ready(cfg: ScepticConfig, w3: Optional[AsyncWeb3] = None) -> AsyncWeb3:
    w3 = w3 or get_async_web3(cfg)
    async for attempt in AsyncRetrying(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=5)):
        with attempt:
            await _probe_provider(w3, cfg.request_timeout_sec)
    return w3

