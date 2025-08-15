from __future__ import annotations

import os
import time
from typing import Any

# Load .env file at startup
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, use system env vars

from mcp.server.fastmcp import FastMCP, Context

from sceptic import ScepticConfig
from sceptic.providers import ensure_web3_ready
from sceptic.erc20 import ERC20
from sceptic.defi import UniV2Router
from sceptic.prices import get_usd_price
from sceptic.permit import sign_permit_eip2612, PermitData
from sceptic.multicall import Multicall2
from sceptic.nft import ERC721, ERC1155
from sceptic.gas import GasStrategy
from sceptic.nonce import NonceManager
from sceptic.wallet import Wallet

# Global variables for lifespan context
_cfg = None
_w3 = None

async def init_context():
    global _cfg, _w3
    if _cfg is None:
        _cfg = ScepticConfig.from_env()
        _w3 = await ensure_web3_ready(_cfg)

def get_context():
    return {"cfg": _cfg, "w3": _w3}

mcp = FastMCP(name="sceptic.py MCP Server")


# Read-only tools (default enabled)
@mcp.tool()
async def health(ctx: Context) -> dict:
    """Check server health and blockchain connectivity"""
    await init_context()
    context = get_context()
    w3 = context["w3"]
    bn = await w3.eth.block_number
    return {"status": "ok", "block": int(bn)}


@mcp.tool()
async def test_simple() -> dict:
    """Simple test function that doesn't require blockchain"""
    return {"message": "Test successful", "timestamp": int(time.time())}


@mcp.tool()
async def test_rpc(ctx: Context = None) -> dict:
    """Test RPC connection and basic blockchain info"""
    await init_context()
    context = get_context()
    cfg = context["cfg"]
    w3 = context["w3"]

    try:
        # Test basic RPC calls
        chain_id = await w3.eth.chain_id
        block_number = await w3.eth.block_number
        gas_price = await w3.eth.gas_price

        return {
            "rpc_url": cfg.rpc_http_url,
            "chain_id": int(chain_id),
            "expected_chain_id": cfg.chain_id,
            "chain_id_match": int(chain_id) == cfg.chain_id,
            "latest_block": int(block_number),
            "gas_price": str(gas_price),
            "status": "connected"
        }
    except Exception as e:
        return {
            "error": f"RPC test failed: {str(e)}",
            "rpc_url": cfg.rpc_http_url,
            "expected_chain_id": cfg.chain_id,
            "status": "failed"
        }


@mcp.tool()
async def wallet_info(ctx: Context = None) -> dict:
    """Get wallet information from .env configuration"""
    await init_context()
    context = get_context()
    cfg = context["cfg"]
    w3 = context["w3"]

    try:
        # Debug info
        current_block = await w3.eth.block_number

        # Get wallet balance
        balance = await w3.eth.get_balance(cfg.account_address)
        nonce = await w3.eth.get_transaction_count(cfg.account_address)

        return {
            "address": cfg.account_address,
            "balance": str(balance),
            "balance_core": str(int(balance) / 10**18),
            "nonce": int(nonce),
            "chain_id": cfg.chain_id,
            "current_block": int(current_block),
            "rpc_url": cfg.rpc_http_url,
            "network": "Core DAO Testnet2" if cfg.chain_id == 1114 else f"Chain {cfg.chain_id}",
            "write_tools_enabled": bool(cfg.private_key)
        }
    except Exception as e:
        return {
            "error": f"Wallet info failed: {str(e)}",
            "chain_id": cfg.chain_id,
            "rpc_url": cfg.rpc_http_url,
            "address": cfg.account_address
        }


@mcp.tool()
async def price_usd(coingecko_id: str, ctx: Context = None) -> dict:
    """Get USD price for cryptocurrency (e.g., 'bitcoin', 'ethereum', 'core-dao')"""
    await init_context()
    context = get_context()
    cfg = context["cfg"]

    try:
        usd = await get_usd_price(cfg, coingecko_id)
        return {
            "coingecko_id": coingecko_id,
            "price_usd": float(usd),
            "timestamp": int(time.time())
        }
    except Exception as e:
        return {"error": f"Price query failed: {str(e)}"}


@mcp.tool()
async def erc20_balance(token_address: str, account_address: str = None, ctx: Context = None) -> dict:
    """Get ERC20 token balance for an account (uses wallet address from .env if not specified)"""
    await init_context()
    context = get_context()
    w3 = context["w3"]
    cfg = context["cfg"]

    # Use wallet address from .env if not provided
    if account_address is None:
        account_address = cfg.account_address

    try:
        # Handle native token (zero address)
        if token_address == "0x0000000000000000000000000000000000000000":
            balance = await w3.eth.get_balance(account_address)
            return {
                "balance": str(balance),
                "balance_formatted": str(int(balance) / 10**18),
                "token_address": token_address,
                "account_address": account_address,
                "token_type": "native",
                "symbol": "CORE",
                "is_wallet_address": account_address.lower() == cfg.account_address.lower()
            }
        else:
            bal = await ERC20(w3, token_address).balance_of(account_address)
            return {
                "balance": str(bal),
                "token_address": token_address,
                "account_address": account_address,
                "token_type": "erc20",
                "is_wallet_address": account_address.lower() == cfg.account_address.lower()
            }
    except Exception as e:
        return {"error": f"Balance query failed: {str(e)}"}


@mcp.tool()
async def erc20_allowance(token_address: str, owner: str, spender: str, ctx: Context) -> dict:
    await init_context()
    context = get_context()
    w3 = context["w3"]
    allowance = await ERC20(w3, token_address).allowance(owner, spender)
    return {"allowance": int(allowance)}


@mcp.tool()
async def defi_quote(token_in: str, token_out: str, amount_in: str, ctx: Context) -> dict:
    """Get DeFi swap quote for token pair"""
    await init_context()
    context = get_context()
    w3 = context["w3"]

    # Default router for Core DAO testnet
    router_address = "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506"  # SushiSwap router

    try:
        amount_in_wei = int(amount_in)
        amounts = await UniV2Router(w3, router_address).get_amounts_out(amount_in_wei, [token_in, token_out])
        return {
            "token_in": token_in,
            "token_out": token_out,
            "amount_in": amount_in,
            "amount_out": str(amounts[1]) if len(amounts) > 1 else "0",
            "router": router_address
        }
    except Exception as e:
        return {"error": f"Quote failed: {str(e)}"}


@mcp.tool()
async def multicall_aggregate(multicall_address: str, calls: list[dict[str, Any]], ctx: Context) -> dict:
    await init_context()
    context = get_context()
    w3 = context["w3"]
    mc = Multicall2(w3, multicall_address)
    prepared: list[tuple[str, bytes]] = []
    for c in calls or []:
        target = c["target"]
        data = c["data"]
        if isinstance(data, str) and data.startswith("0x"):
            prepared.append((target, bytes.fromhex(data[2:])))
        else:
            raise ValueError("call data must be 0x-prefixed hex string")
    block, results = await mc.aggregate(prepared)
    return {"blockNumber": int(block), "returnData": ["0x" + r.hex() for r in results]}


# NFT Tools (read-only)
@mcp.tool()
async def nft_balance_721(token_address: str, owner_address: str, ctx: Context) -> dict:
    """Get ERC721 NFT balance for an owner"""
    await init_context()
    context = get_context()
    w3 = context["w3"]
    nft = ERC721(w3, token_address)
    balance = await nft.balance_of(owner_address)
    return {"balance": int(balance)}


@mcp.tool()
async def nft_owner_of(token_address: str, token_id: int, ctx: Context) -> dict:
    """Get owner of a specific ERC721 token"""
    await init_context()
    context = get_context()
    w3 = context["w3"]
    nft = ERC721(w3, token_address)
    owner = await nft.owner_of(token_id)
    return {"owner": owner}


@mcp.tool()
async def nft_metadata_721(token_address: str, token_id: int, ctx: Context) -> dict:
    """Get metadata URI for ERC721 token"""
    await init_context()
    context = get_context()
    w3 = context["w3"]
    nft = ERC721(w3, token_address)
    uri = await nft.token_uri(token_id)
    return {"token_id": token_id, "uri": uri}


@mcp.tool()
async def nft_balance_1155(token_address: str, owner_address: str, token_id: int, ctx: Context) -> dict:
    """Get ERC1155 NFT balance for specific token ID"""
    await init_context()
    context = get_context()
    w3 = context["w3"]
    nft = ERC1155(w3, token_address)
    balance = await nft.balance_of(owner_address, token_id)
    return {"balance": int(balance)}


@mcp.tool()
async def nft_metadata_1155(token_address: str, token_id: int, ctx: Context) -> dict:
    """Get metadata URI for ERC1155 token"""
    await init_context()
    context = get_context()
    w3 = context["w3"]
    nft = ERC1155(w3, token_address)
    uri = await nft.uri(token_id)
    return {"token_id": token_id, "uri": uri}


# Transaction & Gas Tools
@mcp.tool()
async def gas_estimate(to_address: str, data: str = "0x", value: int = 0, from_address: str | None = None, ctx: Context | None = None) -> dict:
    """Estimate gas for a transaction"""
    await init_context()
    context = get_context()
    w3 = context["w3"]
    cfg = context["cfg"]

    tx_params = {
        "to": w3.to_checksum_address(to_address),
        "data": data,
        "value": value,
    }

    if from_address:
        tx_params["from"] = w3.to_checksum_address(from_address)
    elif cfg.account_address:
        tx_params["from"] = w3.to_checksum_address(cfg.account_address)

    gas_estimate = await w3.eth.estimate_gas(tx_params)
    gas_strategy = GasStrategy()
    gas_prices = await gas_strategy.apply(w3)

    return {
        "gas_estimate": int(gas_estimate),
        "gas_prices": {k: int(v) for k, v in gas_prices.items()}
    }


@mcp.tool()
async def tx_receipt(tx_hash: str, ctx: Context) -> dict:
    """Get transaction receipt"""
    await init_context()
    context = get_context()
    w3 = context["w3"]

    try:
        receipt = await w3.eth.get_transaction_receipt(tx_hash)
        return {
            "tx_hash": receipt["transactionHash"].hex(),
            "block_number": int(receipt["blockNumber"]),
            "gas_used": int(receipt["gasUsed"]),
            "status": int(receipt["status"]),
            "from": receipt["from"],
            "to": receipt["to"],
            "logs_count": len(receipt["logs"])
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def nonce_get(address: str = None, ctx: Context = None) -> dict:
    """Get current nonce for address (uses wallet address from .env if not specified)"""
    await init_context()
    context = get_context()
    w3 = context["w3"]
    cfg = context["cfg"]

    # Use wallet address from .env if not provided
    if address is None:
        address = cfg.account_address

    nonce = await w3.eth.get_transaction_count(w3.to_checksum_address(address))
    return {
        "address": address,
        "nonce": int(nonce),
        "is_wallet_address": address.lower() == cfg.account_address.lower()
    }


# Token Info Tools
@mcp.tool()
async def token_info(token_address: str, ctx: Context) -> dict:
    """Get ERC20 token information (name, symbol, decimals, total supply)"""
    await init_context()
    context = get_context()
    w3 = context["w3"]
    token = ERC20(w3, token_address)

    try:
        name = await token.name()
        symbol = await token.symbol()
        decimals = await token.decimals()
        total_supply = await token.total_supply()

        return {
            "address": token_address,
            "name": name,
            "symbol": symbol,
            "decimals": int(decimals),
            "total_supply": int(total_supply)
        }
    except Exception as e:
        return {"error": str(e)}


# Write tools (enabled via env for safety)
def _require_write():
    context = get_context()
    cfg = context["cfg"]
    if not os.environ.get("SCEPTIC_ENABLE_WRITE_TOOLS"):
        raise ValueError("Write tools disabled; set SCEPTIC_ENABLE_WRITE_TOOLS=1")
    if not cfg.private_key:
        raise ValueError("SCEPTIC_PRIVATE_KEY is required for write tools")
    return cfg


@mcp.tool()
async def erc20_approve(token_address: str, spender: str, amount_wei: int, ctx: Context) -> dict:
    from eth_account import Account

    await init_context()
    context = get_context()
    w3 = context["w3"]
    cfg = _require_write()
    acct = Account.from_key(cfg.private_key)
    txh = await ERC20(w3, token_address).approve(acct, spender, int(amount_wei))
    return {"tx_hash": txh}


@mcp.tool()
async def erc20_transfer(token_address: str, to: str, amount_wei: int, ctx: Context) -> dict:
    from eth_account import Account

    await init_context()
    context = get_context()
    w3 = context["w3"]
    cfg = _require_write()
    acct = Account.from_key(cfg.private_key)
    txh = await ERC20(w3, token_address).transfer(acct, to, int(amount_wei))
    return {"tx_hash": txh}


@mcp.tool()
async def defi_swap_exact_tokens_for_tokens(
    router_address: str,
    token_in: str,
    token_out: str,
    to: str,
    amount_in_wei: int,
    amount_out_min_wei: int = 1,
    deadline: int | None = None,
    ctx: Context | None = None,
) -> dict:
    from eth_account import Account

    await init_context()
    context = get_context()
    w3 = context["w3"]
    cfg = _require_write()
    acct = Account.from_key(cfg.private_key)
    path = [token_in, token_out]
    dl = int(deadline or (int(time.time()) + 1200))
    txh = await UniV2Router(w3, router_address).swap_exact_tokens_for_tokens(
        acct, int(amount_in_wei), int(amount_out_min_wei), path, to, dl
    )
    return {"tx_hash": txh}


@mcp.tool()
async def erc20_permit_sign(
    token_name: str,
    token_address: str,
    owner: str,
    spender: str,
    value: int,
    nonce: int,
    deadline: int,
    token_version: str = "1",
    ctx: Context | None = None,
) -> dict:
    from eth_account import Account

    await init_context()
    context = get_context()
    w3 = context["w3"]
    cfg = _require_write()
    acct = Account.from_key(cfg.private_key)
    v, r, s = await sign_permit_eip2612(
        w3,
        acct,
        token_name,
        token_version,
        cfg.chain_id,
        token_address,
        PermitData(
            owner=owner,
            spender=spender,
            value=int(value),
            nonce=int(nonce),
            deadline=int(deadline),
        ),
    )
    return {"v": v, "r": f"0x{r:064x}", "s": f"0x{s:064x}"}


# NFT Write Tools
@mcp.tool()
async def nft_transfer_721(token_address: str, to: str, token_id: int, ctx: Context) -> dict:
    """Transfer ERC721 NFT (requires private key)"""
    from eth_account import Account

    await init_context()
    context = get_context()
    w3 = context["w3"]
    cfg = _require_write()
    acct = Account.from_key(cfg.private_key)

    nft = ERC721(w3, token_address)
    txh = await nft.safe_transfer_from(acct, acct.address, to, token_id)
    return {"tx_hash": txh}


@mcp.tool()
async def nft_transfer_1155(token_address: str, to: str, token_id: int, amount: int, ctx: Context) -> dict:
    """Transfer ERC1155 NFT (requires private key)"""
    from eth_account import Account

    await init_context()
    context = get_context()
    w3 = context["w3"]
    cfg = _require_write()
    acct = Account.from_key(cfg.private_key)

    nft = ERC1155(w3, token_address)
    txh = await nft.safe_transfer_from(acct, acct.address, to, token_id, amount)
    return {"tx_hash": txh}


# Wallet & Signing Tools
@mcp.tool()
async def wallet_sign_message(message: str, ctx: Context) -> dict:
    """Sign a message with wallet private key"""
    await init_context()
    context = get_context()
    cfg = _require_write()

    wallet = Wallet.from_private_key(cfg.private_key)
    signature = wallet.sign_message(message)
    return {"message": message, "signature": signature, "signer": wallet.address}


@mcp.tool()
async def wallet_sign_typed_data(typed_data: dict, ctx: Context) -> dict:
    """Sign EIP-712 typed data with wallet private key"""
    await init_context()
    context = get_context()
    cfg = _require_write()

    wallet = Wallet.from_private_key(cfg.private_key)
    signature = wallet.sign_typed_data(typed_data)
    return {"typed_data": typed_data, "signature": signature, "signer": wallet.address}


@mcp.tool()
async def wallet_create(ctx: Context) -> dict:
    """Generate a new random wallet (returns address and private key - use carefully!)"""
    from eth_account import Account

    # This doesn't require write permissions since it's just generating a new wallet
    acct = Account.create()
    return {
        "address": acct.address,
        "private_key": acct.key.hex(),
        "warning": "Store private key securely! Never share it!"
    }


# Portfolio & Analytics Tools
@mcp.tool()
async def portfolio_value(wallet_address: str, token_addresses: list[str], ctx: Context) -> dict:
    """Calculate total portfolio value in USD for given tokens"""
    await init_context()
    context = get_context()
    w3 = context["w3"]
    cfg = context["cfg"]

    portfolio = []
    total_usd = 0.0

    for token_addr in token_addresses:
        try:
            token = ERC20(w3, token_addr)
            balance = await token.balance_of(wallet_address)
            decimals = await token.decimals()
            symbol = await token.symbol()

            # Convert balance to human readable
            balance_human = balance / (10 ** decimals)

            # Try to get USD price (this might fail for unknown tokens)
            try:
                # This is a simplified approach - in reality you'd need a mapping of token addresses to coingecko IDs
                usd_price = 0.0  # Placeholder - would need proper price lookup
                usd_value = balance_human * usd_price
            except:
                usd_price = 0.0
                usd_value = 0.0

            portfolio.append({
                "token_address": token_addr,
                "symbol": symbol,
                "balance": float(balance_human),
                "usd_price": usd_price,
                "usd_value": usd_value
            })

            total_usd += usd_value

        except Exception as e:
            portfolio.append({
                "token_address": token_addr,
                "error": str(e)
            })

    return {
        "wallet_address": wallet_address,
        "tokens": portfolio,
        "total_usd_value": total_usd
    }


@mcp.tool()
async def block_info(block_number: int | str = "latest", ctx: Context | None = None) -> dict:
    """Get block information"""
    await init_context()
    context = get_context()
    w3 = context["w3"]

    if isinstance(block_number, str) and block_number == "latest":
        block = await w3.eth.get_block("latest")
    else:
        block = await w3.eth.get_block(int(block_number))

    return {
        "number": int(block["number"]),
        "hash": block["hash"].hex(),
        "timestamp": int(block["timestamp"]),
        "gas_used": int(block["gasUsed"]),
        "gas_limit": int(block["gasLimit"]),
        "transaction_count": len(block["transactions"])
    }


def main():
    mcp.run()  # stdio transport (Claude Desktop compatible)


if __name__ == "__main__":
    main()
