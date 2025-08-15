from __future__ import annotations

import asyncio
import json
import time
import contextlib
from typing import Any, Awaitable, Callable, Dict, Optional

from eth_account import Account
from eth_account.signers.local import LocalAccount
# Use legacy server API for broader compatibility (websockets v10-v15)
from websockets.legacy.server import serve as ws_serve, WebSocketServerProtocol
from web3 import AsyncWeb3

from .config import ScepticConfig
from .logging import get_logger
from .erc20 import ERC20
from .prices import get_usd_price
from .providers import ensure_web3_ready
from .defi import UniV2Router
from .nonce import NonceManager
from .gas import GasStrategy
from .validation import assert_chain_id
from .rawrpc import RawRpc
from .permit import sign_permit_eip2612, PermitData
from .multicall import Multicall2


JsonRpcHandler = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]


class RpcServer:
    def __init__(self, cfg: ScepticConfig):
        self.cfg = cfg
        self.log = get_logger("sceptic.server")
        self.handlers: dict[str, JsonRpcHandler] = {}
        self._subscribers: set[WebSocketServerProtocol] = set()
        self.w3: Optional[AsyncWeb3] = None
        self._broadcaster_task: Optional[asyncio.Task] = None
        self._last_block: Optional[int] = None

    def method(self, name: str):
        def deco(fn: JsonRpcHandler):
            self.handlers[name] = fn
            return fn
        return deco

    async def _auth_ok(self, headers: dict[str, str]) -> bool:
        token = self.cfg.server_api_token
        if not token:
            return True
        auth = headers.get("authorization") or headers.get("Authorization")
        return auth == f"Bearer {token}"

    def set_web3(self, w3: AsyncWeb3) -> None:
        self.w3 = w3

    async def _broadcast_block(self, block_number: int) -> None:
        note = json.dumps({"jsonrpc": "2.0", "method": "events.block", "params": {"number": block_number}})
        dead: list[WebSocketServerProtocol] = []
        for sub in list(self._subscribers):
            try:
                await sub.send(note)
            except Exception:
                dead.append(sub)
        for d in dead:
            self._subscribers.discard(d)
        if dead:
            self.log.info(f"Cleaned {len(dead)} dead subscribers")

    async def _block_broadcaster(self, interval_sec: int = 5) -> None:
        if not self.w3:
            return
        # Initialize last block
        try:
            self._last_block = await self.w3.eth.block_number
        except Exception:
            self._last_block = None
        while True:
            try:
                bn = await self.w3.eth.block_number
                if self._last_block is None:
                    self._last_block = bn
                elif bn > self._last_block:
                    for b in range(self._last_block + 1, bn + 1):
                        await self._broadcast_block(b)
                    self._last_block = bn
            except Exception as e:
                self.log.debug(f"Block poll error: {e}")
            await asyncio.sleep(interval_sec)

    async def _handle(self, ws: WebSocketServerProtocol):
        async for raw in ws:
            id_ = None
            try:
                req = json.loads(raw)
                method = req.get("method")
                params = req.get("params") or {}
                id_ = req.get("id")
                # Method gating via config
                enabled = self.cfg.server_enable_methods
                if enabled and "*" not in enabled and method not in enabled:
                    await ws.send(json.dumps({"jsonrpc": "2.0", "id": id_, "error": {"code": -32601, "message": "Method disabled"}}))
                    continue
                if method not in self.handlers:
                    await ws.send(json.dumps({"jsonrpc": "2.0", "id": id_, "error": {"code": -32601, "message": "Method not found"}}))
                    continue
                if method == "events.subscribe":
                    self._subscribers.add(ws)
                    await ws.send(json.dumps({"jsonrpc": "2.0", "id": id_, "result": {"ok": True}}))
                    continue
                if method == "events.unsubscribe":
                    self._subscribers.discard(ws)
                    await ws.send(json.dumps({"jsonrpc": "2.0", "id": id_, "result": {"ok": True}}))
                    continue
                res = await self.handlers[method](params)
                await ws.send(json.dumps({"jsonrpc": "2.0", "id": id_, "result": res}))
            except Exception as e:
                await ws.send(json.dumps({"jsonrpc": "2.0", "id": id_, "error": {"code": -32000, "message": str(e)}}))

    async def start(self):
        async def ws_handler(ws: WebSocketServerProtocol, path: str | None = None):
            headers = getattr(ws, "request_headers", None)
            if self.cfg.server_api_token:
                if not headers or not await self._auth_ok(dict(headers)):
                    await ws.close(code=4401, reason="Unauthorized")
                    return
            try:
                await self._handle(ws)
            finally:
                # cleanup
                self._subscribers.discard(ws)

        async with ws_serve(ws_handler, self.cfg.server_host, self.cfg.server_port):
            # Start broadcaster if web3 is set
            if self.w3 and not self._broadcaster_task:
                self._broadcaster_task = asyncio.create_task(self._block_broadcaster())
            try:
                await asyncio.Future()  # run forever
            finally:
                if self._broadcaster_task:
                    self._broadcaster_task.cancel()
                    with contextlib.suppress(Exception):
                        await self._broadcaster_task


async def build_default_server(cfg: ScepticConfig) -> RpcServer:
    server = RpcServer(cfg)
    w3 = await ensure_web3_ready(cfg)
    server.set_web3(w3)
    await assert_chain_id(w3, cfg.chain_id)
    nonce_mgr = NonceManager(w3)
    gas_strategy = GasStrategy()
    raw = RawRpc(cfg.rpc_http_url, timeout=cfg.request_timeout_sec)

    def account_from_cfg() -> Optional[LocalAccount]:
        if cfg.private_key:
            return Account.from_key(cfg.private_key)
        return None

    @server.method("health")
    async def health(_: dict[str, Any]) -> dict[str, Any]:
        bn = await w3.eth.block_number
        return {"status": "ok", "block": bn}

    @server.method("price.usd")
    async def price_usd(params: dict[str, Any]) -> dict[str, Any]:
        coin = params["coingecko_id"]
        p = await get_usd_price(cfg, coin)
        return {"coingecko_id": coin, "usd": p}

    @server.method("erc20.balance")
    async def erc20_balance(params: dict[str, Any]) -> dict[str, Any]:
        token = ERC20(w3, params["token_address"])
        bal = await token.balance_of(params["account_address"])
        return {"balance": bal}

    @server.method("erc20.allowance")
    async def erc20_allowance(params: dict[str, Any]) -> dict[str, Any]:
        token = ERC20(w3, params["token_address"])
        allowance = await token.allowance(params["owner"], params["spender"])
        return {"allowance": allowance}

    @server.method("erc20.transfer")
    async def erc20_transfer(params: dict[str, Any]) -> dict[str, Any]:
        acct = account_from_cfg()
        if not acct:
            raise ValueError("No private key configured for transfer")
        token = ERC20(w3, params["token_address"])
        txh = await token.transfer(
            acct,
            params["to"],
            int(params["amount_wei"]),
        )
        return {"tx_hash": txh}

    @server.method("erc20.approve")
    async def erc20_approve(params: dict[str, Any]) -> dict[str, Any]:
        acct = account_from_cfg()
        if not acct:
            raise ValueError("No private key configured for approve")
        token = ERC20(w3, params["token_address"])
        txh = await token.approve(
            acct,
            params["spender"],
            int(params["amount_wei"]),
        )
        return {"tx_hash": txh}

    @server.method("defi.quote")
    async def defi_quote(params: dict[str, Any]) -> dict[str, Any]:
        router = UniV2Router(w3, params["router_address"])
        path = [params["token_in"], params["token_out"]]
        amounts = await router.get_amounts_out(int(params["amount_in_wei"]), path)
        return {"amounts": amounts}

    @server.method("defi.swapExactTokensForTokens")
    async def defi_swap(params: dict[str, Any]) -> dict[str, Any]:
        acct = account_from_cfg()
        if not acct:
            raise ValueError("No private key configured for swap")
        router = UniV2Router(w3, params["router_address"])
        nonce = await nonce_mgr.get_next(acct.address)
        gas = await gas_strategy.apply(w3)
        txh = await router.swap_exact_tokens_for_tokens(
            acct,
            int(params["amount_in_wei"]),
            int(params["amount_out_min_wei"]),
            [params["token_in"], params["token_out"]],
            params["to"],
            int(params.get("deadline", 0) or (int(time.time()) + 1200)),
            **gas,
            nonce=nonce,
        )
        return {"tx_hash": txh}

    @server.method("rpc.call")
    async def rpc_call(params: dict[str, Any]) -> dict[str, Any]:
        method = params.get("method")
        if method not in cfg.server_rpc_allow_methods:
            raise ValueError("RPC method not allowed")
        result = await raw.call(method, params.get("params") or [])
        return {"method": method, "result": result}

    @server.method("erc20.permitSign")
    async def erc20_permit_sign(params: dict[str, Any]) -> dict[str, Any]:
        acct = account_from_cfg()
        if not acct:
            raise ValueError("No private key configured for permit sign")
        v, r, s = await sign_permit_eip2612(
            w3,
            acct,
            params["token_name"],
            params.get("token_version", "1"),
            cfg.chain_id,
            params["token_address"],
            PermitData(
                owner=params["owner"],
                spender=params["spender"],
                value=int(params["value"]),
                nonce=int(params["nonce"]),
                deadline=int(params["deadline"]),
            ),
        )
        return {"v": v, "r": f"0x{r:064x}", "s": f"0x{s:064x}"}

    @server.method("multicall.aggregate")
    async def multicall_aggregate(params: dict[str, Any]) -> dict[str, Any]:
        mc = Multicall2(w3, params["multicall_address"])
        calls = []
        for c in params.get("calls") or []:
            target = c["target"]
            data = c["data"]
            if isinstance(data, str) and data.startswith("0x"):
                data_bytes = bytes.fromhex(data[2:])
            else:
                raise ValueError("call data must be 0x-prefixed hex string")
            calls.append((target, data_bytes))
        block, results = await mc.aggregate(calls)
        hex_results = ["0x" + r.hex() for r in results]
        return {"blockNumber": block, "returnData": hex_results}

    return server

