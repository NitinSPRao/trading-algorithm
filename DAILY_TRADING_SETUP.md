# Daily Trading Setup Guide

This guide explains how to run your trading algorithm once per day at market open (9:30 AM ET).

## How the Algorithm Works

Based on your backtesting results, the algorithm:

1. **Uses OPEN prices** - All trading decisions are based on the opening price of TECL each day
2. **Checks at market open** - Best time to run is at 9:30 AM ET when the market opens
3. **Follows proven strategy** - The same logic that achieved 24,012% returns in backtesting

### Trading Logic Recap

**Buy Signals:**
- Immediate buy if TECL < 0.75 × 30-day SMA
- Buy if TECL < 1.25 × 30-day SMA AND VIX 4 days ago > 1.04 × 30-day WMA

**Sell Signal:**
- Sell when TECL ≥ 1.058 × purchase price (5.8% gain)

**Rules:**
- Skip buy signals the day after selling
- Use 95% of buying power per position

## Option 1: macOS/Linux Cron Job (Recommended)

Run automatically every weekday at 9:30 AM ET.

### Setup Steps

1. **Test the script first:**
   ```bash
   ./scripts/run_daily_trader.sh
   ```

2. **Edit your crontab:**
   ```bash
   crontab -e
   ```

3. **Add this line for 9:30 AM ET:**

   If you're in Eastern Time (ET):
   ```cron
   30 9 * * 1-5 cd /Users/nitinrao/Downloads/trading-algorithm && ./scripts/run_daily_trader.sh >> logs/cron.log 2>&1
   ```

   If you're in Pacific Time (PT) - runs at 6:30 AM PT = 9:30 AM ET:
   ```cron
   30 6 * * 1-5 cd /Users/nitinrao/Downloads/trading-algorithm && ./scripts/run_daily_trader.sh >> logs/cron.log 2>&1
   ```

   If you're in Central Time (CT) - runs at 8:30 AM CT = 9:30 AM ET:
   ```cron
   30 8 * * 1-5 cd /Users/nitinrao/Downloads/trading-algorithm && ./scripts/run_daily_trader.sh >> logs/cron.log 2>&1
   ```

4. **Save and exit** (in vi/vim: press ESC, type `:wq`, press ENTER)

5. **Verify cron is set:**
   ```bash
   crontab -l
   ```

### Cron Format Explanation
```
30 9 * * 1-5
│  │ │ │ │
│  │ │ │ └─── Day of week (1-5 = Monday-Friday)
│  │ │ └───── Month (1-12, * = every month)
│  │ └─────── Day of month (1-31, * = every day)
│  └───────── Hour (9 = 9 AM)
└─────────── Minute (30 = :30)
```

## Option 2: Manual Daily Execution

Run manually each trading day:

```bash
# From project root
./scripts/run_daily_trader.sh

# Or directly with Python
python -m trading_algorithm.daily_trader
```

## Option 3: Using Launchd (macOS Alternative)

More reliable than cron on macOS.

### Create a launchd plist file:

```bash
cat > ~/Library/LaunchAgents/com.user.trading-algorithm.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.trading-algorithm</string>

    <key>ProgramArguments</key>
    <array>
        <string>/Users/nitinrao/Downloads/trading-algorithm/scripts/run_daily_trader.sh</string>
    </array>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>30</integer>
        <key>Weekday</key>
        <integer>1</integer>
    </dict>

    <key>WorkingDirectory</key>
    <string>/Users/nitinrao/Downloads/trading-algorithm</string>

    <key>StandardOutPath</key>
    <string>/Users/nitinrao/Downloads/trading-algorithm/logs/launchd.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/nitinrao/Downloads/trading-algorithm/logs/launchd_error.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
EOF
```

### Load the job:
```bash
launchctl load ~/Library/LaunchAgents/com.user.trading-algorithm.plist
```

### Manage the job:
```bash
# Check status
launchctl list | grep trading-algorithm

# Unload (stop)
launchctl unload ~/Library/LaunchAgents/com.user.trading-algorithm.plist

# Reload (after changes)
launchctl unload ~/Library/LaunchAgents/com.user.trading-algorithm.plist
launchctl load ~/Library/LaunchAgents/com.user.trading-algorithm.plist
```

## Monitoring & Logs

### Check Logs

All trading activity is logged:

```bash
# Daily trading log
tail -f logs/daily_trading.log

# Cron execution log (if using cron)
tail -f logs/cron.log

# Launchd log (if using launchd)
tail -f logs/launchd.log
```

### Verify Execution

```bash
# Check recent trades
grep -E "BUY|SELL" logs/daily_trading.log | tail -20

# Check today's execution
grep "$(date +%Y-%m-%d)" logs/daily_trading.log
```

## Important Notes

### 1. **Paper Trading vs Live Trading**

The current setup uses **Alpaca Paper Trading** (test account) by default:
```python
self.trading_client = TradingClient(self.api_key, self.secret_key, paper=True)
```

To switch to live trading:
- Change `paper=True` to `paper=False` in [live_trader.py:41](trading_algorithm/live_trader.py#L41)
- Update your `.env` with live API keys
- **Start with small amounts!**

### 2. **Market Holidays**

The algorithm checks if the market is open. On holidays, it will log and exit without trading.

### 3. **Timezone Considerations**

- Market opens at 9:30 AM **Eastern Time**
- Adjust your cron schedule based on your local timezone
- The algorithm internally uses ET for market hours

### 4. **Position Sizing**

Current config uses 95% of available buying power:
```bash
# In .env file
POSITION_SIZE_LIMIT=0.95
```

Adjust this value (0.0 to 1.0) to change position sizing.

### 5. **Safety Features**

The algorithm includes safety checks:
- ✅ Verifies market is open before trading
- ✅ Checks sufficient buying power
- ✅ Validates historical data availability
- ✅ Logs all decisions and trades
- ✅ Handles API errors gracefully

## Testing

### Test the daily trader:
```bash
# Dry run (will check signals but Alpaca paper trading is safe)
python -m trading_algorithm.daily_trader
```

### Check what the algorithm would do right now:
```bash
# This runs the trading check immediately
./scripts/run_daily_trader.sh
```

## Troubleshooting

### Cron not running?

1. **Check cron service is running:**
   ```bash
   # macOS
   sudo launchctl list | grep cron
   ```

2. **Check permissions:**
   ```bash
   ls -la scripts/run_daily_trader.sh
   # Should show -rwxr-xr-x (executable)
   ```

3. **Test manually:**
   ```bash
   cd /Users/nitinrao/Downloads/trading-algorithm
   ./scripts/run_daily_trader.sh
   ```

4. **Check logs:**
   ```bash
   tail -f logs/cron.log
   ```

### Script fails?

1. **Check environment variables:**
   ```bash
   cat .env | grep ALPACA
   ```

2. **Check Python environment:**
   ```bash
   source .venv/bin/activate
   python -c "import alpaca; print('Alpaca installed')"
   ```

3. **Check API credentials:**
   ```bash
   python tests/test_alpaca_credentials.py
   ```

## Summary

**Recommended Setup:** Use **cron** (Option 1) for simplicity.

**Schedule:** 9:30 AM ET, Monday-Friday (adjust for your timezone)

**Safety:** Algorithm uses paper trading by default - safe to test

**Monitoring:** Check `logs/daily_trading.log` regularly

**Performance:** Backtested 24,012% return vs 247% buy-and-hold (2016-2025)

Ready to automate your trading! 🚀
