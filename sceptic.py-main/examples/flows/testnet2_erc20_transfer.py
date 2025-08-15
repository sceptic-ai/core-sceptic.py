import asyncio
import os
import sys

from eth_account import Account
from sceptic import ScepticConfig
from sceptic.providers import ensure_web3_ready
from sceptic.erc20 import ERC20
from sceptic.tx import wait_for_receipt, ensure_confirmations


async def main():
    # Read ENV
    cfg = ScepticConfig.from_env()
    if not cfg.rpc_http_url:
        print("SCEPTIC_RPC_HTTP_URL is empty; will auto-fill for chain 1114 if selected", file=sys.stderr)
    if not cfg.private_key:
        print("Missing SCEPTIC_PRIVATE_KEY", file=sys.stderr)
        sys.exit(2)
    if not cfg.account_address:
        print("Missing SCEPTIC_ACCOUNT_ADDRESS", file=sys.stderr)
        sys.exit(2)

    token_addr = os.environ.get("TOKEN_ADDRESS")
    recipient = os.environ.get("RECIPIENT_ADDRESS")
    amount_wei = os.environ.get("AMOUNT_WEI")
    if not token_addr or not recipient or not amount_wei:
        print("Please set TOKEN_ADDRESS, RECIPIENT_ADDRESS, AMOUNT_WEI", file=sys.stderr)
        sys.exit(2)

    w3 = await ensure_web3_ready(cfg)
    acct = Account.from_key(cfg.private_key)

    token = ERC20(w3, token_addr)
    print("Sender:", cfg.account_address)
    print("Token:", token_addr)

    bal_before = await token.balance_of(cfg.account_address)
    print("Balance before:", bal_before)

    txh = await token.transfer(acct, recipient, int(amount_wei))
    print("Transfer tx hash:", txh)

    rcpt = await wait_for_receipt(w3, txh, timeout_sec=180)
    rcpt = await ensure_confirmations(w3, rcpt, confirmations=1)
    print("Receipt status:", rcpt.get("status"), "block:", rcpt.get("blockNumber"))

    bal_after = await token.balance_of(cfg.account_address)
    print("Balance after:", bal_after)


if __name__ == "__main__":
    asyncio.run(main())

