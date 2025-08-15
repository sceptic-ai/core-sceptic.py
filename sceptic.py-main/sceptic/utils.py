from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from web3 import AsyncWeb3


@dataclass
class TxParams:
    gas: Optional[int] = None
    gas_price: Optional[int] = None
    max_fee_per_gas: Optional[int] = None
    max_priority_fee_per_gas: Optional[int] = None
    nonce: Optional[int] = None


def to_wei(w3: AsyncWeb3, amount: float | int | str, unit: str = "ether") -> int:
    return w3.to_wei(amount, unit)


def from_wei(w3: AsyncWeb3, amount_wei: int, unit: str = "ether") -> float:
    return float(w3.from_wei(amount_wei, unit))

