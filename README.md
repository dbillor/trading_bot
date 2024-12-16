# Autonomous Crypto Trading Bot

This repository contains an autonomous crypto trading application that connects to decentralized exchanges, fetches real-time price data, and executes trades based on a simple momentum strategy. By leveraging Ethereum-compatible blockchains and tokens (like WETH and USDC), it demonstrates a full pipeline: from gathering market data, generating buy/sell signals, to executing on-chain trades.

## Key Features

- **Momentum-Based Strategy:**  
  Continuously monitors token prices and identifies signals when short-term price momentum passes defined thresholds. If the price surges above a certain percentage, the bot attempts a buy; if it falls below a set threshold, it initiates a sell.

- **On-Chain Execution:**  
  Uses Web3 libraries to interact directly with smart contracts on Ethereum mainnet or Layer-2 solutions (e.g., Arbitrum, Optimism). The bot can approve tokens, execute swaps on Uniswap V3, and confirm transactions, all from the command line.

- **Configurable Parameters:**  
  Easily adjust parameters such as:
  - Trading pair (`trade_token_in`, `trade_token_out`)
  - Momentum thresholds
  - Trade size (`base_position_size_wei`)
  - RPC endpoints and network settings
  - Slippage tolerance

- **Logging and Monitoring:**  
  Detailed logs provide insights into every step: fetching prices, detecting signals, sending transactions, and handling exceptions (like pending transactions or insufficient balance).

## Prerequisites

- **Python 3.10+** with a virtual environment recommended.
- **Web3.py** and related dependencies (installed via `pip install -r requirements.txt`).
- **A Private Key and RPC Endpoint:**  
  You need a valid Ethereum account funded with ETH for gas and tokens (WETH, USDC) to trade.  
  Add your configurations and credentials to `config.json` (never commit sensitive data!).

GOOD LUCK! (BTW- Trading ETh is expensive, be prepared to put in a lot of money and be prepared to lose money.
