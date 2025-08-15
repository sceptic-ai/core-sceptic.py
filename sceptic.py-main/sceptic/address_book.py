from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AddressBook:
    router_v2: Optional[str] = None
    wrapped_native: Optional[str] = None
    stable_usd: Optional[str] = None
    multicall2: Optional[str] = None


# Chain-specific address book entries.
# Note: Do NOT guess addresses. Provide only authoritative ones when available.
# Users can override by config/environment.
ADDRESS_BOOK: dict[int, AddressBook] = {
    # 1114 = Core Testnet2. Populate when official addresses are published.
    1114: AddressBook(
        router_v2=None,
        wrapped_native=None,
        stable_usd=None,
        multicall2=None,
    ),
    # 1116 = Core Mainnet. Leave empty unless definitively known.
    1116: AddressBook(
        router_v2=None,
        wrapped_native=None,
        stable_usd=None,
        multicall2=None,
    ),
}


def get_address_book(chain_id: int) -> AddressBook:
    return ADDRESS_BOOK.get(chain_id, AddressBook())

