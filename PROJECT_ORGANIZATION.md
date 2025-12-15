# Project Organization Summary

This document describes the cleaned-up structure of the trading algorithm project.

## Directory Structure

```
trading-algorithm/
├── .env                    # Environment variables (API keys)
├── .gitignore             # Git ignore rules
├── README.md              # Main project documentation
├── LICENSE                # License file
├── pyproject.toml         # Project configuration
├── uv.lock                # Dependency lock file
│
├── trading_algorithm/     # Main Python package
│   ├── __init__.py
│   ├── backtesting.py    # Backtesting engine (daily data, logging, buy-and-hold comparison)
│   ├── trader.py         # Live trading implementation
│   └── ...
│
├── tests/                 # Test scripts
│   ├── README.md         # Test documentation
│   ├── test_alpaca_credentials.py
│   ├── test_alpha_vantage_vix.py
│   ├── test_buy_sell.py
│   ├── test_data_availability.py
│   ├── test_finnhub_vix.py
│   └── test_yahoo_vix.py
│
├── scripts/              # Utility shell scripts
│   ├── README.md        # Scripts documentation
│   ├── run_trader.sh    # Run the trading algorithm
│   ├── rotate_logs.sh   # Log rotation
│   └── setup_monitoring.sh
│
├── logs/                 # Log files (auto-generated, gitignored)
│   ├── backtesting.log
│   ├── trading.log
│   └── trading_scheduler.log
│
├── data/                 # Data files (gitignored)
│   └── *.csv
│
└── docs/                 # Documentation
```

## Key Changes

### Files Moved
- ✅ All `test_*.py` files → `tests/`
- ✅ All `*.sh` scripts → `scripts/`
- ✅ All `*.log` files → `logs/`

### Configuration Updated
- ✅ `.gitignore` updated to ignore `logs/` directory
- ✅ `backtesting.py` updated to write logs to `logs/backtesting.log`
- ✅ README documentation added to `tests/` and `scripts/` folders
- ✅ Main README.md updated with project structure

### Benefits
1. **Cleaner root directory** - Only essential config files at root
2. **Better organization** - Related files grouped together
3. **Easier navigation** - Clear purpose for each directory
4. **Version control** - Log files properly ignored
5. **Documentation** - Each folder has its own README

## Running the Project

### Backtesting
```bash
# With live API data
python -m trading_algorithm.backtesting --live-data

# With local CSV files
python -m trading_algorithm.backtesting
```

### Tests
```bash
python tests/test_alpaca_credentials.py
```

### Scripts
```bash
chmod +x scripts/*.sh
./scripts/run_trader.sh
```

## Log Files

All logs are now stored in `logs/` directory:
- `backtesting.log` - Detailed trade logs from backtesting
- `trading.log` - Live trading logs
- `trading_scheduler.log` - Scheduler logs

The `logs/` directory is gitignored to prevent committing large log files.
