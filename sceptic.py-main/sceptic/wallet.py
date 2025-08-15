from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from .wallet_protocol import WalletProtocol
from eth_account import Account
from eth_account.messages import encode_defunct, encode_typed_data
from eth_account.signers.local import LocalAccount


@dataclass
class Wallet(WalletProtocol):
    account: LocalAccount

    @classmethod
    def from_private_key(cls, pk: str) -> "Wallet":
        return cls(Account.from_key(pk))

    @property
    def address(self) -> str:
        return self.account.address

    def sign_message(self, message: str) -> str:
        msg = encode_defunct(text=message)
        sig = self.account.sign_message(msg)
        return sig.signature.hex()

    def sign_typed_data(self, typed_data: dict) -> str:
        msg = encode_typed_data(primitive=typed_data)
        sig = self.account.sign_message(msg)
        return sig.signature.hex()

