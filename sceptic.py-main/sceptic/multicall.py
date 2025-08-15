from __future__ import annotations

from typing import Any, List, Tuple
from web3 import AsyncWeb3

# Minimal Multicall2 ABI
MULTICALL2_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "target", "type": "address"},
                    {"internalType": "bytes", "name": "callData", "type": "bytes"},
                ],
                "internalType": "struct Multicall2.Call[]",
                "name": "calls",
                "type": "tuple[]",
            }
        ],
        "name": "aggregate",
        "outputs": [
            {"internalType": "uint256", "name": "blockNumber", "type": "uint256"},
            {"internalType": "bytes[]", "name": "returnData", "type": "bytes[]"},
        ],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]


class Multicall2:
    def __init__(self, w3: AsyncWeb3, address: str):
        self.w3 = w3
        self.address = w3.to_checksum_address(address)
        self.contract = w3.eth.contract(address=self.address, abi=MULTICALL2_ABI)

    async def aggregate(self, calls: List[Tuple[str, bytes]]) -> Tuple[int, List[bytes]]:
        targets = [self.w3.to_checksum_address(t) for (t, _) in calls]
        datas = [d for (_, d) in calls]
        block, results = await self.contract.functions.aggregate(
            list(zip(targets, datas))
        ).call()
        return (block, results)

