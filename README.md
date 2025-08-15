# Sceptic.py

Advanced Blockchain Toolkit with MCP Integration for Core DAO

## Overview

Sceptic.py is a comprehensive Python library designed for seamless blockchain interactions on Core DAO networks. It provides both programmatic APIs and AI assistant integration through the Model Context Protocol (MCP), enabling natural language blockchain operations.

### Core Features

- **Async Web3.py Integration**: High-performance asynchronous blockchain operations
- **Multi-Token Support**: ERC-20, ERC-721, and ERC-1155 token standards
- **DeFi Protocol Integration**: Uniswap V2-compatible router implementations
- **Market Data Access**: Real-time price feeds via CoinGecko and DexScreener
- **MCP Server**: Native Model Context Protocol server for AI assistant integration
- **Transaction Management**: Advanced gas estimation, nonce handling, and retry logic
- **Multi-Network Support**: Core DAO mainnet and testnet compatibility

## Installation

### Requirements
- Python 3.11 or higher
- Core DAO RPC access

### Basic Installation
```bash
git clone https://github.com/your-repo/core-sceptic.py
cd core-sceptic.py
pip install -e .
```

### Development Installation
```bash
pip install -e .[dev]
```

### Optional Dependencies
```bash
pip install -e .[defi]    # DeFi protocol integrations
pip install -e .[prices]  # Price feed providers
pip install -e .[agent]   # AI agent features
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Network Configuration
SCEPTIC_CHAIN_ID=1114
SCEPTIC_RPC_HTTP_URL=https://rpc.test2.btcs.network

# Wallet Configuration (for write operations)
SCEPTIC_PRIVATE_KEY=0x...
SCEPTIC_ACCOUNT_ADDRESS=0x...

# MCP Server Configuration
SCEPTIC_ENABLE_WRITE_TOOLS=1

# Optional: Performance tuning
SCEPTIC_GAS_MULTIPLIER=1.2
SCEPTIC_PRIORITY_GWEI=1.0
SCEPTIC_REQUEST_TIMEOUT_SEC=30
```

### Network Endpoints

#### Core DAO Testnet2 (Chain ID: 1114)
- RPC: `https://rpc.test2.btcs.network`
- WebSocket: `wss://rpc.test2.btcs.network/wsp`
- Explorer: `https://scan.test2.btcs.network`

#### Core DAO Mainnet (Chain ID: 1116)
- RPC: `https://rpc.coredao.org`
- Explorer: `https://scan.coredao.org`

## Usage

### MCP Server Integration

Start the MCP server for AI assistant integration:

```bash
python -m sceptic mcp
```

### Claude Desktop Integration

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "core-sceptic.py": {
      "command": "/path/to/core-sceptic.py/run_mcp.sh"
    }
  }
}
```

### Available MCP Tools

#### Read-Only Operations
- `health`: Server and blockchain connectivity status
- `wallet_info`: Wallet configuration and balance information
- `nonce_get`: Current transaction nonce for address
- `erc20_balance`: Token balance queries
- `erc20_allowance`: Token approval status
- `price_usd`: Cryptocurrency price data
- `defi_quote`: DeFi swap price quotes
- `token_info`: ERC-20 token metadata
- `gas_estimate`: Transaction gas estimation
- `tx_receipt`: Transaction receipt details
- `block_info`: Blockchain block information

#### Write Operations (Requires Private Key)
- `erc20_approve`: Token spending approvals
- `erc20_transfer`: Token transfers
- `defi_swap_exact_tokens_for_tokens`: DeFi token swaps
- `erc20_permit_sign`: Gasless approval signatures
- `wallet_sign_message`: Message signing
- `wallet_sign_typed_data`: EIP-712 structured data signing
- `multicall_aggregate`: Batch transaction execution

### Programmatic Usage

```python
from sceptic import ScepticConfig
from sceptic.erc20 import ERC20
import asyncio

async def main():
    config = ScepticConfig.from_env()
    w3 = config.get_async_w3()

    # ERC-20 token interaction
    token = ERC20(w3, "0x...")
    balance = await token.balance_of("0x...")
    print(f"Balance: {balance}")

asyncio.run(main())
```

## Architecture

### Core Components

- **ScepticConfig**: Environment-based configuration management
- **AsyncWeb3Provider**: Optimized Web3 provider with retry logic
- **ERC20/ERC721/ERC1155**: Token standard implementations
- **UniV2Router**: Uniswap V2-compatible DEX interactions
- **Multicall2**: Batch transaction aggregation
- **PriceFeeds**: Market data aggregation

### Security Features

- **Private Key Encryption**: Secure key storage and handling
- **Transaction Simulation**: Pre-execution validation
- **Gas Optimization**: Intelligent gas price management
- **Rate Limiting**: Request throttling and DOS protection
- **Input Validation**: Comprehensive parameter sanitization

## Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
black sceptic/
flake8 sceptic/
mypy sceptic/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Submit a pull request

## License

Apache License - see LICENSE file for details.

## Disclaimer

This software is provided "as is" without warranty. Always test on testnets before mainnet deployment. Users are responsible for securing private keys and understanding transaction implications.
