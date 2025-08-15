import asyncio
import os
import sys

from eth_account import Account
from sceptic import ScepticConfig
from sceptic.providers import ensure_web3_ready
from sceptic.erc20 import ERC20
from sceptic.tx import wait_for_receipt, ensure_confirmations


async def main():
    cfg = ScepticConfig.from_env()
    if not cfg.private_key or not cfg.account_address:
        print("Missing SCEPTIC_PRIVATE_KEY or SCEPTIC_ACCOUNT_ADDRESS", file=sys.stderr)
        sys.exit(2)
    token_addr = os.environ.get("TOKEN_ADDRESS")
    spender = os.environ.get("SPENDER")
    amount_wei = os.environ.get("AMOUNT_WEI")
    if not token_addr or not spender or not amount_wei:
        print("Please set TOKEN_ADDRESS, SPENDER, AMOUNT_WEI", file=sys.stderr)
        sys.exit(2)

    w3 = await ensure_web3_ready(cfg)
    acct = Account.from_key(cfg.private_key)
    erc20 = ERC20(w3, token_addr)

    current = await erc20.allowance(cfg.account_address, spender)
    print("Allowance before:", current)

    txh = await erc20.approve(acct, spender, int(amount_wei))
    print("Approve tx hash:", txh)

    rcpt = await wait_for_receipt(w3, txh)
    rcpt = await ensure_confirmations(w3, rcpt, confirmations=1)
    print("Receipt status:", rcpt.get("status"), "block:", rcpt.get("blockNumber"))

    after = await erc20.allowance(cfg.account_address, spender)
    print("Allowance after:", after)


if __name__ == "__main__":
    asyncio.run(main())

