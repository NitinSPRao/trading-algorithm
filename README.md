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
git clone https://github.com/YOUR_USERNAME/trading-algorithm.git
cd trading-algorithm
```

2. Install required packages:
```bash
pip install pandas numpy
```

## Usage

1. Prepare your data files:
   - `tecl_history5.csv`: Historical data for TECL
   - `vix_history.csv`: Historical data for VIX

2. Run the backtesting script:
```bash
python backtesting.py
```

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