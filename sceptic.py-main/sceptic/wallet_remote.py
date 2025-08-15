from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from .wallet_protocol import WalletProtocol


class RemoteSigner(Protocol):
    def get_address(self) -> str: ...
    def sign_message(self, message: str) -> str: ...
    def sign_typed_data(self, typed_data: dict) -> str: ...


@dataclass
class RemoteWallet(WalletProtocol):
    signer: RemoteSigner

    @property
    def address(self) -> str:
        return self.signer.get_address()

    def sign_message(self, message: str) -> str:
        return self.signer.sign_message(message)

    def sign_typed_data(self, typed_data: dict) -> str:
        return self.signer.sign_typed_data(typed_data)

