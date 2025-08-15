from __future__ import annotations

import time
from dataclasses import dataclass
from eth_account.messages import encode_typed_data
from eth_account.signers.local import LocalAccount
from web3 import AsyncWeb3

# EIP-2612 permit helper

@dataclass
class PermitData:
    owner: str
    spender: str
    value: int
    nonce: int
    deadline: int


async def sign_permit_eip2612(
    w3: AsyncWeb3,
    account: LocalAccount,
    token_name: str,
    token_version: str,
    chain_id: int,
    token_address: str,
    permit: PermitData,
):
    domain = {
        "name": token_name,
        "version": token_version,
        "chainId": int(chain_id),
        "verifyingContract": w3.to_checksum_address(token_address),
    }
    types = {
        "EIP712Domain": [
            {"name": "name", "type": "string"},
            {"name": "version", "type": "string"},
            {"name": "chainId", "type": "uint256"},
            {"name": "verifyingContract", "type": "address"},
        ],
        "Permit": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"},
            {"name": "value", "type": "uint256"},
            {"name": "nonce", "type": "uint256"},
            {"name": "deadline", "type": "uint256"},
        ],
    }
    message = {
        "owner": w3.to_checksum_address(permit.owner),
        "spender": w3.to_checksum_address(permit.spender),
        "value": int(permit.value),
        "nonce": int(permit.nonce),
        "deadline": int(permit.deadline),
    }
    typed = {"types": types, "domain": domain, "primaryType": "Permit", "message": message}
    signable = encode_typed_data(primitive=typed)
    signed = account.sign_message(signable)
    v, r, s = signed.v, signed.r, signed.s
    return v, r, s

