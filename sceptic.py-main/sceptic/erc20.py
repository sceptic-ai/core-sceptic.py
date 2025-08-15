from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from eth_account import Account
from eth_account.signers.local import LocalAccount
from web3 import AsyncWeb3
from web3.contract.async_contract import AsyncContract
from web3.types import TxParams as Web3TxParams

from .utils import TxParams


def load_abi(name: str) -> list[dict]:
    abi_path = Path(__file__).with_name("abis") / f"{name}.json"
    return json.loads(abi_path.read_text())


class ERC20:
    def __init__(self, w3: AsyncWeb3, address: str):
        self.w3 = w3
        self.address = self.w3.to_checksum_address(address)
        self.contract: AsyncContract = self.w3.eth.contract(
            address=self.address, abi=load_abi("erc20")
        )

    async def decimals(self) -> int:
        return await self.contract.functions.decimals().call()

    async def name(self) -> str:
        return await self.contract.functions.name().call()

    async def symbol(self) -> str:
        return await self.contract.functions.symbol().call()

    async def balance_of(self, account: str) -> int:
        return await self.contract.functions.balanceOf(self.w3.to_checksum_address(account)).call()

    async def allowance(self, owner: str, spender: str) -> int:
        return await self.contract.functions.allowance(
            self.w3.to_checksum_address(owner), self.w3.to_checksum_address(spender)
        ).call()

    async def approve(
        self,
        account: LocalAccount,
        spender: str,
        amount: int,
        tx_params: Optional[TxParams] = None,
    ) -> str:
        base = await self._base_tx_params(account.address, tx_params)
        fn = self.contract.functions.approve(self.w3.to_checksum_address(spender), amount)
        if "gas" not in base:
            base["gas"] = await fn.estimate_gas({"from": base["from"]})
        tx = fn.build_transaction(base)
        signed = Account.sign_transaction(tx, private_key=account.key)
        tx_hash = await self.w3.eth.send_raw_transaction(signed.rawTransaction)
        return tx_hash.hex()

    async def transfer(
        self, account: LocalAccount, to: str, amount: int, tx_params: Optional[TxParams] = None
    ) -> str:
        base = await self._base_tx_params(account.address, tx_params)
        fn = self.contract.functions.transfer(self.w3.to_checksum_address(to), amount)
        if "gas" not in base:
            base["gas"] = await fn.estimate_gas({"from": base["from"]})
        tx = fn.build_transaction(base)
        signed = Account.sign_transaction(tx, private_key=account.key)
        tx_hash = await self.w3.eth.send_raw_transaction(signed.rawTransaction)
        return tx_hash.hex()

    async def _base_tx_params(self, from_addr: str, params: Optional[TxParams]) -> Web3TxParams:
        base: Web3TxParams = {
            "from": self.w3.to_checksum_address(from_addr),
            "chainId": await self.w3.eth.chain_id,
            "nonce": params.nonce if params and params.nonce is not None else await self.w3.eth.get_transaction_count(self.w3.to_checksum_address(from_addr)),
        }
        if params and params.gas is not None:
            base["gas"] = params.gas
        if params and params.gas_price is not None:
            base["gasPrice"] = params.gas_price
        if params and params.max_fee_per_gas is not None:
            base["maxFeePerGas"] = params.max_fee_per_gas
        if params and params.max_priority_fee_per_gas is not None:
            base["maxPriorityFeePerGas"] = params.max_priority_fee_per_gas
        return base

