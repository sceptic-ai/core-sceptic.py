import asyncio
import os

from sceptic import ScepticConfig, get_async_web3
from sceptic.erc20 import ERC20


async def main():
    cfg = ScepticConfig.from_env()
    w3 = get_async_web3(cfg)
    token_addr = os.environ["TOKEN_ADDRESS"]
    account_addr = os.environ["ACCOUNT_ADDRESS"]
    erc20 = ERC20(w3, token_addr)
    bal = await erc20.balance_of(account_addr)
    print({"balance": bal})


if __name__ == "__main__":
    asyncio.run(main())

