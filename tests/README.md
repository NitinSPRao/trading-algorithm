# Test Scripts

This directory contains various test scripts for validating different components of the trading algorithm.

## Available Tests

### API Connection Tests

- **test_alpaca_credentials.py** - Validates Alpaca API credentials and connection
- **test_alpha_vantage_vix.py** - Tests Alpha Vantage API for VIX data retrieval
- **test_finnhub_vix.py** - Tests Finnhub API for VIX data retrieval
- **test_yahoo_vix.py** - Tests Yahoo Finance API for VIX data retrieval

### Trading Tests

- **test_buy_sell.py** - Tests buy/sell functionality with the trading algorithm
- **test_data_availability.py** - Validates that required market data is available

## Running Tests

Run individual tests:
```bash
python tests/test_alpaca_credentials.py
python tests/test_buy_sell.py
```

## Notes

- Make sure your `.env` file is configured with the necessary API keys before running tests
- These tests may make actual API calls and consume API rate limits
