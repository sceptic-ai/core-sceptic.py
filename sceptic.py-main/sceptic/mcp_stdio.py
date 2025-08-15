from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Any, Dict

from .config import ScepticConfig
from .providers import ensure_web3_ready
from .wallet import Wallet
from .erc20 import ERC20
from .defi import UniV2Router
from .prices import get_usd_price
from .permit import sign_permit_eip2612, PermitData
from .multicall import Multicall2


class MCPServer:
    def __init__(self, cfg: ScepticConfig):
        self.cfg = cfg
        self.handlers: Dict[str, Any] = {}

    def method(self, name: str):
        def deco(fn):
            self.handlers[name] = fn
            return fn
        return deco

    async def run(self):
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)
        writer_transport, writer_protocol = await asyncio.get_event_loop().connect_write_pipe(asyncio.streams.FlowControlMixin, sys.stdout)
        writer = asyncio.StreamWriter(writer_transport, writer_protocol, reader, asyncio.get_event_loop())

        while True:
            line = await reader.readline()
            if not line:
                break
            try:
                req = json.loads(line.decode())
                method = req.get("method")
                params = req.get("params") or {}
                id_ = req.get("id")
                if method not in self.handlers:
                    await self._send(writer, {"jsonrpc": "2.0", "id": id_, "error": {"code": -32601, "message": "Method not found"}})
                    continue
                res = await self.handlers[method](params)
                await self._send(writer, {"jsonrpc": "2.0", "id": id_, "result": res})
            except Exception as e:
                await self._send(writer, {"jsonrpc": "2.0", "error": {"code": -32000, "message": str(e)}})

    async def _send(self, writer: asyncio.StreamWriter, obj: dict):
        writer.write((json.dumps(obj) + "\n").encode())
        await writer.drain()


async def build_mcp_server(cfg: ScepticConfig) -> MCPServer:
    server = MCPServer(cfg)
    w3 = await ensure_web3_ready(cfg)

    @server.method("health")
    async def health(_: dict[str, Any]) -> dict[str, Any]:
        bn = await w3.eth.block_number
        return {"status": "ok", "block": bn}

    @server.method("wallet.address")
    async def wallet_address(_: dict[str, Any]) -> dict[str, Any]:
        if not cfg.private_key:
            raise ValueError("No private key configured")
        w = Wallet.from_private_key(cfg.private_key)
        return {"address": w.address}

    @server.method("price.usd")
    async def price_usd(params: dict[str, Any]) -> dict[str, Any]:
        return {"usd": await get_usd_price(cfg, params["coingecko_id"]) }

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

    @server.method("erc20.approve")
    async def erc20_approve(params: dict[str, Any]) -> dict[str, Any]:
        pk = cfg.private_key
        if not pk:
            raise ValueError("No private key configured")
        from eth_account import Account
        acct = Account.from_key(pk)
        token = ERC20(w3, params["token_address"])
        txh = await token.approve(acct, params["spender"], int(params["amount_wei"]))
        return {"tx_hash": txh}

    @server.method("erc20.transfer")
    async def erc20_transfer(params: dict[str, Any]) -> dict[str, Any]:
        pk = cfg.private_key
        if not pk:
            raise ValueError("No private key configured")
        from eth_account import Account
        acct = Account.from_key(pk)
        token = ERC20(w3, params["token_address"])
        txh = await token.transfer(acct, params["to"], int(params["amount_wei"]))
        return {"tx_hash": txh}

    @server.method("defi.quote")
    async def defi_quote(params: dict[str, Any]) -> dict[str, Any]:
        router = UniV2Router(w3, params["router_address"])
        path = [params["token_in"], params["token_out"]]
        amounts = await router.get_amounts_out(int(params["amount_in_wei"]), path)
        return {"amounts": amounts}

    @server.method("defi.swapExactTokensForTokens")
    async def defi_swap(params: dict[str, Any]) -> dict[str, Any]:
        pk = cfg.private_key
        if not pk:
            raise ValueError("No private key configured")
        from eth_account import Account
        acct = Account.from_key(pk)
        router = UniV2Router(w3, params["router_address"])
        txh = await router.swap_exact_tokens_for_tokens(
            acct,
            int(params["amount_in_wei"]),
            int(params["amount_out_min_wei"]),
            [params["token_in"], params["token_out"]],
            params["to"],
            int(params.get("deadline", 0) or (int(__import__('time').time()) + 1200)),
        )
        return {"tx_hash": txh}

    @server.method("erc20.permitSign")
    async def erc20_permit_sign(params: dict[str, Any]) -> dict[str, Any]:
        pk = cfg.private_key
        if not pk:
            raise ValueError("No private key configured")
        from eth_account import Account
        acct = Account.from_key(pk)
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

