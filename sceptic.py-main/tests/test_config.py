from sceptic.config import ScepticConfig


def test_from_env_defaults(monkeypatch):
    monkeypatch.delenv("SCEPTIC_RPC_WS_URL", raising=False)
    monkeypatch.setenv("SCEPTIC_RPC_HTTP_URL", "http://localhost:8545")
    monkeypatch.setenv("SCEPTIC_CHAIN_ID", "1116")
    cfg = ScepticConfig.from_env()
    assert cfg.rpc_http_url == "http://localhost:8545"
    assert cfg.chain_id == 1116

