from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from eth_account import Account
from eth_account.signers.local import LocalAccount
from web3 import AsyncWeb3
from web3.contract.async_contract import AsyncContract

from .utils import TxParams


def load_abi(name: str) -> list[dict]:
    abi_path = Path(__file__).with_name("abis") / f"{name}.json"
    return json.loads(abi_path.read_text())


class ERC721:
    def __init__(self, w3: AsyncWeb3, address: str):
        self.w3 = w3
        self.address = self.w3.to_checksum_address(address)
        self.contract: AsyncContract = self.w3.eth.contract(
            address=self.address, abi=load_abi("erc721")
        )

    async def owner_of(self, token_id: int) -> str:
        return await self.contract.functions.ownerOf(token_id).call()

    async def balance_of(self, owner: str) -> int:
        return await self.contract.functions.balanceOf(self.w3.to_checksum_address(owner)).call()

    async def get_approved(self, token_id: int) -> str:
        return await self.contract.functions.getApproved(token_id).call()

    async def approve(
        self, account: LocalAccount, to: str, token_id: int, tx_params: Optional[TxParams] = None
    ) -> str:
        base = await self._base_tx_params(account.address, tx_params)
        fn = self.contract.functions.approve(self.w3.to_checksum_address(to), token_id)
        if "gas" not in base:
            base["gas"] = await fn.estimate_gas({"from": base["from"]})
        tx = fn.build_transaction(base)
        signed = Account.sign_transaction(tx, private_key=account.key)
        tx_hash = await self.w3.eth.send_raw_transaction(signed.rawTransaction)
        return tx_hash.hex()

    async def safe_transfer_from(
        self,
        account: LocalAccount,
        from_addr: str,
        to: str,
        token_id: int,
        tx_params: Optional[TxParams] = None,
    ) -> str:
        base = await self._base_tx_params(account.address, tx_params)
        fn = self.contract.functions.safeTransferFrom(
            self.w3.to_checksum_address(from_addr),
            self.w3.to_checksum_address(to),
            token_id,
        )
        if "gas" not in base:
            base["gas"] = await fn.estimate_gas({"from": base["from"]})
        tx = fn.build_transaction(base)
        signed = Account.sign_transaction(tx, private_key=account.key)
        tx_hash = await self.w3.eth.send_raw_transaction(signed.rawTransaction)
        return tx_hash.hex()

    async def token_uri(self, token_id: int) -> str:
        return await self.contract.functions.tokenURI(token_id).call()

    async def _base_tx_params(self, from_addr: str, params: Optional[TxParams]):
        base = {
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


class ERC1155:
    def __init__(self, w3: AsyncWeb3, address: str):
        self.w3 = w3
        self.address = self.w3.to_checksum_address(address)
        self.contract: AsyncContract = self.w3.eth.contract(
            address=self.address, abi=load_abi("erc1155")
        )

    async def balance_of(self, owner: str, token_id: int) -> int:
        return await self.contract.functions.balanceOf(self.w3.to_checksum_address(owner), token_id).call()

    async def is_approved_for_all(self, owner: str, operator: str) -> bool:
        return await self.contract.functions.isApprovedForAll(
            self.w3.to_checksum_address(owner), self.w3.to_checksum_address(operator)
        ).call()

    async def set_approval_for_all(
        self, account: LocalAccount, operator: str, approved: bool, tx_params: Optional[TxParams] = None
    ) -> str:
        base = await self._base_tx_params(account.address, tx_params)
        fn = self.contract.functions.setApprovalForAll(self.w3.to_checksum_address(operator), approved)
        if "gas" not in base:
            base["gas"] = await fn.estimate_gas({"from": base["from"]})
        tx = fn.build_transaction(base)
        signed = Account.sign_transaction(tx, private_key=account.key)
        tx_hash = await self.w3.eth.send_raw_transaction(signed.rawTransaction)
        return tx_hash.hex()

    async def safe_transfer_from(
        self,
        account: LocalAccount,
        from_addr: str,
        to: str,
        token_id: int,
        amount: int,
        data: bytes = b"",
        tx_params: Optional[TxParams] = None,
    ) -> str:
        base = await self._base_tx_params(account.address, tx_params)
        fn = self.contract.functions.safeTransferFrom(
            self.w3.to_checksum_address(from_addr),
            self.w3.to_checksum_address(to),
            token_id,
            amount,
            data,
        )
        if "gas" not in base:
            base["gas"] = await fn.estimate_gas({"from": base["from"]})
        tx = fn.build_transaction(base)
        signed = Account.sign_transaction(tx, private_key=account.key)
        tx_hash = await self.w3.eth.send_raw_transaction(signed.rawTransaction)
        return tx_hash.hex()

    async def uri(self, token_id: int) -> str:
        return await self.contract.functions.uri(token_id).call()

    async def _base_tx_params(self, from_addr: str, params: Optional[TxParams]):
        base = {
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

