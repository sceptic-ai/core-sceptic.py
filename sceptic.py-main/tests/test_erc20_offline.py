import pytest

from sceptic.erc20 import ERC20
from web3 import AsyncWeb3, AsyncHTTPProvider


@pytest.mark.asyncio
async def test_erc20_init_checksum():
    w3 = AsyncWeb3(AsyncHTTPProvider("http://localhost:8545"))
    token = ERC20(w3, "0x0000000000000000000000000000000000000000")
    assert token.address.startswith("0x")

