# Trading Algorithm Backtesting System

A Python-based backtesting system for trading strategies, specifically designed for analyzing TECL (Direxion Daily Technology Bull 3X Shares) and VIX (Volatility Index) data.

## Overview

This system implements a backtesting framework that:
- Loads and processes historical price data for TECL and VIX
- Calculates technical indicators (SMA and WMA)
- Implements a trading strategy based on price movements relative to moving averages
- Tracks portfolio performance and profits

## Features

- Data loading and preprocessing for multiple financial instruments
- Technical indicator calculations:
  - 30-day Simple Moving Average (SMA) for TECL
  - 30-day Weighted Moving Average (WMA) for VIX
- Trading strategy implementation with:
  - Entry conditions based on price relative to moving averages
  - Exit conditions based on profit targets
  - Bank account for profit management
- Performance tracking and reporting

## Requirements

- Python 3.x
- pandas
- numpy

## Installation

1. Clone the repository:
```bash
git clone https://github.com/NitinSPRao/trading-algorithm.git
cd trading-algorithm
```

2. Install required packages:
```bash
pip install pandas numpy
```

## Project Structure

```
trading-algorithm/
├── trading_algorithm/    # Main package
│   ├── backtesting.py   # Backtesting engine with live data support
│   └── trader.py        # Live trading implementation
├── tests/               # Test scripts
│   ├── test_alpaca_credentials.py
│   ├── test_buy_sell.py
│   └── ...
├── scripts/             # Utility scripts
│   ├── run_trader.sh
│   ├── rotate_logs.sh
│   └── setup_monitoring.sh
├── logs/               # Log files (auto-generated)
├── data/               # CSV data files
└── docs/               # Documentation
```

## Usage

### Running Backtests

With live data from APIs:
```bash
python -m trading_algorithm.backtesting --live-data
```

With local CSV files:
```bash
python -m trading_algorithm.backtesting
```

### Running Tests

```bash
python tests/test_alpaca_credentials.py
python tests/test_buy_sell.py
```

### Running Scripts

```bash
./scripts/run_trader.sh
```

### Automated Daily Trading

Run the algorithm automatically at market open (9:30 AM ET):

**Option 1: Local Machine (cron/launchd)**
- See [DAILY_TRADING_SETUP.md](DAILY_TRADING_SETUP.md)
- Requires your computer to be on

**Option 2: GitHub Actions (Cloud - Recommended)**
- See [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md)
- Runs in the cloud automatically
- Free and reliable

## Trading Strategy

The system implements the following trading logic:

### Entry Conditions:
- Immediate buy if TECL < 0.75 * SMA_tecl
- Buy if TECL < 1.25 * SMA_tecl AND VIX > 1.04 * WMA_vix (4 days prior)

### Exit Conditions:
- Sell when TECL price >= 1.0575 * purchase price

### Additional Rules:
- 20% of profits are moved to a bank account
- Buy signals are ignored on the day immediately following a sell

## Output

The system provides:
- Detailed trade records including dates, actions, and prices
- Final fund value
- Total amount in bank account
- Annualized return calculations

## Data Format

Input CSV files should contain the following columns:
- Date column (will be converted to datetime)
- Open prices
- Other price data (High, Low, Close, etc.)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This software is for educational and research purposes only. It is not intended to provide financial advice. Always do your own research before making investment decisions.
