from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ChainProfile:
    chain_id: int
    name: str
    native_symbol: str = "CORE"
    rpc_http_default: Optional[str] = None
    rpc_ws_default: Optional[str] = None
    explorer_base_url: Optional[str] = None


CORE_MAINNET = ChainProfile(
    chain_id=1116,
    name="Core Mainnet",
    native_symbol="CORE",
    rpc_http_default=None,  # Provide via config for production use
    rpc_ws_default=None,
    explorer_base_url=None,
)

CORE_TESTNET = ChainProfile(
    chain_id=1115,
    name="Core Testnet (deprecated)",
    native_symbol="tCORE",
    rpc_http_default=None,
    rpc_ws_default=None,
    explorer_base_url=None,
)

CORE_TESTNET2 = ChainProfile(
    chain_id=1114,
    name="Core Testnet2",
    native_symbol="tCORE2",
    rpc_http_default="https://rpc.test2.btcs.network",
    rpc_ws_default="wss://rpc.test2.btcs.network/wsp",
    explorer_base_url="https://scan.test2.btcs.network",
)


def get_chain_profile(chain_id: int) -> ChainProfile:
    if chain_id == CORE_MAINNET.chain_id:
        return CORE_MAINNET
    if chain_id == CORE_TESTNET2.chain_id:
        return CORE_TESTNET2
    if chain_id == CORE_TESTNET.chain_id:
        return CORE_TESTNET
    return ChainProfile(chain_id=chain_id, name=f"Chain {chain_id}")

