from __future__ import annotations

from typing import Optional
from eth_account import Account
from eth_account.signers.local import LocalAccount


def local_account_from_private_key(private_key: Optional[str]) -> Optional[LocalAccount]:
    if not private_key:
        return None
    return Account.from_key(private_key)

