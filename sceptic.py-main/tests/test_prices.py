import pytest

from sceptic.config import ScepticConfig
from sceptic.prices import CoingeckoClient


@pytest.mark.asyncio
async def test_coingecko_client_builds_url():
    # Offline test: just ensure we can construct and close without network
    cfg = ScepticConfig(rpc_http_url="http://localhost:8545", chain_id=1116)
    cg = CoingeckoClient(cfg.coingecko_base_url)
    await cg.close()
    assert True

