from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional
from web3 import AsyncWeb3


@dataclass
class GasStrategy:
    priority_gwei: float = 1.0  # for EIP-1559
    max_multiplier: float = 1.2
    legacy_gwei: Optional[float] = None  # if set, use legacy gasPrice

    async def apply(self, w3: AsyncWeb3) -> dict:
        if self.legacy_gwei is not None:
            return {"gasPrice": w3.to_wei(self.legacy_gwei, "gwei")}
        base = await w3.eth.gas_price
        max_fee = math.floor(base * self.max_multiplier)
        max_priority = w3.to_wei(self.priority_gwei, "gwei")
        return {"maxFeePerGas": max_fee, "maxPriorityFeePerGas": max_priority}

