from __future__ import annotations

from typing import Optional

from eth_account import Account
from eth_account.signers.local import LocalAccount
from web3 import AsyncWeb3
from web3.contract.async_contract import AsyncContract


UNISWAP_V2_ROUTER_ABI = [
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"},
        ],
        "name": "getAmountsOut",
        "outputs": [
            {"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type": "uint256"},
        ],
        "name": "swapExactTokensForTokens",
        "outputs": [
            {"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"},
        ],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]


class UniV2Router:
    def __init__(self, w3: AsyncWeb3, address: str):
        self.w3 = w3
        self.address = self.w3.to_checksum_address(address)
        self.contract: AsyncContract = self.w3.eth.contract(address=self.address, abi=UNISWAP_V2_ROUTER_ABI)

    async def get_amounts_out(self, amount_in: int, path: list[str]) -> list[int]:
        checksummed = [self.w3.to_checksum_address(p) for p in path]
        return await self.contract.functions.getAmountsOut(amount_in, checksummed).call()

    async def swap_exact_tokens_for_tokens(
        self,
        account: LocalAccount,
        amount_in: int,
        amount_out_min: int,
        path: list[str],
        to: str,
        deadline: int,
        gas: Optional[int] = None,
        gas_price: Optional[int] = None,
        max_fee_per_gas: Optional[int] = None,
        max_priority_fee_per_gas: Optional[int] = None,
        nonce: Optional[int] = None,
    ) -> str:
        base = {
            "from": self.w3.to_checksum_address(account.address),
            "chainId": await self.w3.eth.chain_id,
            "nonce": nonce if nonce is not None else await self.w3.eth.get_transaction_count(self.w3.to_checksum_address(account.address)),
            **({"gas": gas} if gas is not None else {}),
            **({"gasPrice": gas_price} if gas_price is not None else {}),
            **({"maxFeePerGas": max_fee_per_gas} if max_fee_per_gas is not None else {}),
            **({"maxPriorityFeePerGas": max_priority_fee_per_gas} if max_priority_fee_per_gas is not None else {}),
        }
        fn = self.contract.functions.swapExactTokensForTokens(
            amount_in,
            amount_out_min,
            [self.w3.to_checksum_address(p) for p in path],
            self.w3.to_checksum_address(to),
            deadline,
        )
        if "gas" not in base:
            base["gas"] = await fn.estimate_gas({"from": base["from"]})
        tx = fn.build_transaction(base)
        signed = Account.sign_transaction(tx, private_key=account.key)
        tx_hash = await self.w3.eth.send_raw_transaction(signed.rawTransaction)
        return tx_hash.hex()

