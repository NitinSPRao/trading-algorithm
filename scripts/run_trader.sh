#!/bin/bash
cd "/Users/nitinrao/Downloads/trading-algorithm"
source .venv/bin/activate
export PATH="/Users/nitinrao/Downloads/trading-algorithm/.venv/bin:$PATH"
/Users/nitinrao/Downloads/trading-algorithm/.venv/bin/python -m trading_algorithm.live_trader >> "/Users/nitinrao/Downloads/trading-algorithm/trading.log" 2>&1
