#!/bin/bash
cd "/Users/nitinrao/Downloads/trading-algorithm"
if [ -f trading.log ] && [ $(wc -l < trading.log) -gt 1000 ]; then
    mv trading.log "trading_$(date +%Y%m%d_%H%M%S).log"
    touch trading.log
fi
