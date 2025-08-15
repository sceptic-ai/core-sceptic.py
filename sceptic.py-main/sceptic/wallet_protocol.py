from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class WalletProtocol(Protocol):
    @property
    def address(self) -> str: ...

    def sign_message(self, message: str) -> str: ...

    def sign_typed_data(self, typed_data: dict) -> str: ...

    # sign_transaction: not all wallets expose raw tx signing in same format; left for adapter-specific impl

