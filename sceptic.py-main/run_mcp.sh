#!/bin/bash

# Sceptic MCP Server Wrapper Script
# This script ensures the correct environment is loaded

# Change to the project directory
cd "/Users/baturalpguvenc/Documents/GitHub/sceptic.py"

# Activate virtual environment
source .venv/bin/activate

# Load environment variables from .env
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set required environment variables
export SCEPTIC_CHAIN_ID=1114
export SCEPTIC_ENABLE_WRITE_TOOLS=1

# Run the MCP server
exec python -m sceptic mcp
