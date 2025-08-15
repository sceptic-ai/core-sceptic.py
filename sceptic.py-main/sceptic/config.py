from __future__ import annotations

import os
from typing import Optional
from pydantic import BaseModel, Field
from .network import get_chain_profile


class ScepticConfig(BaseModel):
    # Core/EVM chain configuration
    rpc_http_url: str = Field(..., description="HTTP RPC endpoint for CoreDAO (EVM)")
    rpc_ws_url: Optional[str] = Field(None, description="WebSocket RPC endpoint")
    chain_id: int = Field(..., description="EVM chain ID for CoreDAO")

    # Account
    private_key: Optional[str] = Field(
        default=None, description="Hex private key for signing transactions"
    )
    account_address: Optional[str] = Field(default=None, description="Account address")

    # Gas/Fees
    gas_price_wei: Optional[int] = Field(None, description="Fixed gas price in wei (optional)")
    max_fee_per_gas_wei: Optional[int] = Field(None)
    max_priority_fee_per_gas_wei: Optional[int] = Field(None)

    # Timeouts
    request_timeout_sec: int = Field(default=30)

    # Price/data services
    coingecko_base_url: str = Field(
        default="https://api.coingecko.com/api/v3", description="Coingecko API base"
    )
    dexscreener_base_url: str = Field(
        default="https://api.dexscreener.com/latest/dex", description="Dexscreener API"
    )

    # MCP-like server
    server_host: str = Field(default="127.0.0.1")
    server_port: int = Field(default=8765)
    server_api_token: Optional[str] = Field(default=None)
    server_allow_origins: list[str] = Field(default_factory=lambda: ["*"])
    server_enable_methods: list[str] = Field(default_factory=lambda: ["*"])
    server_rpc_allow_methods: list[str] = Field(
        default_factory=lambda: [
            "eth_blockNumber",
            "eth_getTransactionByHash",
            "eth_getBalance",
            "eth_getBlockByNumber",
            "eth_getBlockByHash",
            "eth_call",
        ]
    )

    class Config:
        extra = "ignore"

    @classmethod
    def from_env(cls) -> "ScepticConfig":
        chain_id = int(os.environ.get("SCEPTIC_CHAIN_ID", "1116"))
        rpc_http = os.environ.get("SCEPTIC_RPC_HTTP_URL", "")
        rpc_ws = os.environ.get("SCEPTIC_RPC_WS_URL")
        # Auto-fill from known chain profiles if missing
        if not rpc_http:
            prof = get_chain_profile(chain_id)
            if prof.rpc_http_default:
                rpc_http = prof.rpc_http_default
            if not rpc_ws and prof.rpc_ws_default:
                rpc_ws = prof.rpc_ws_default
        return cls(
            rpc_http_url=rpc_http,
            rpc_ws_url=rpc_ws,
            chain_id=chain_id,
            private_key=os.environ.get("SCEPTIC_PRIVATE_KEY"),
            account_address=os.environ.get("SCEPTIC_ACCOUNT_ADDRESS"),
            gas_price_wei=(
                int(os.environ["SCEPTIC_GAS_PRICE_WEI"]) if os.environ.get("SCEPTIC_GAS_PRICE_WEI") else None
            ),
            max_fee_per_gas_wei=(
                int(os.environ["SCEPTIC_MAX_FEE_PER_GAS_WEI"]) if os.environ.get("SCEPTIC_MAX_FEE_PER_GAS_WEI") else None
            ),
            max_priority_fee_per_gas_wei=(
                int(os.environ["SCEPTIC_MAX_PRIORITY_FEE_PER_GAS_WEI"]) if os.environ.get("SCEPTIC_MAX_PRIORITY_FEE_PER_GAS_WEI") else None
            ),
            request_timeout_sec=int(os.environ.get("SCEPTIC_REQUEST_TIMEOUT_SEC", "30")),
            coingecko_base_url=os.environ.get("SCEPTIC_COINGECKO_BASE_URL", "https://api.coingecko.com/api/v3"),
            dexscreener_base_url=os.environ.get("SCEPTIC_DEXSCREENER_BASE_URL", "https://api.dexscreener.com/latest/dex"),
            server_host=os.environ.get("SCEPTIC_SERVER_HOST", "127.0.0.1"),
            server_port=int(os.environ.get("SCEPTIC_SERVER_PORT", "8765")),
            server_api_token=os.environ.get("SCEPTIC_SERVER_API_TOKEN"),
            server_allow_origins=os.environ.get("SCEPTIC_SERVER_ALLOW_ORIGINS", "*").split(","),
            server_enable_methods=[m.strip() for m in os.environ.get("SCEPTIC_SERVER_ENABLE_METHODS", "*").split(",") if m.strip()],
            server_rpc_allow_methods=[m.strip() for m in os.environ.get("SCEPTIC_SERVER_RPC_ALLOW", "eth_blockNumber,eth_getTransactionByHash,eth_getBalance,eth_getBlockByNumber,eth_getBlockByHash,eth_call").split(",") if m.strip()],
        )

