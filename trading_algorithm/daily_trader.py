#!/usr/bin/env python3
"""Daily trading script - runs once per day at market open."""

import os
import logging
from datetime import datetime
import pytz
from .live_trader import AlpacaLiveTrader

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'daily_trading.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_daily_trade():
    """Execute the daily trading check at market open."""
    et_tz = pytz.timezone('US/Eastern')
    now_et = datetime.now(et_tz)

    logger.info("=" * 80)
    logger.info(f"🤖 DAILY TRADING CHECK - {now_et.strftime('%Y-%m-%d %I:%M %p ET')}")
    logger.info("=" * 80)

    # Skip weekends
    if now_et.weekday() >= 5:
        logger.info("📅 Weekend detected - market is closed")
        return

    try:
        trader = AlpacaLiveTrader()

        # Check if market is open
        clock = trader.trading_client.get_clock()
        if not clock.is_open:
            logger.info("🔒 Market is currently closed")
            logger.info(f"Next market open: {clock.next_open}")
            return

        # Get account info
        account_info = trader.get_account_info()
        logger.info(f"💰 Account Portfolio Value: ${account_info['portfolio_value']:,.2f}")
        logger.info(f"💵 Available Buying Power: ${account_info['buying_power']:,.2f}")
        logger.info(f"💵 Cash: ${account_info['cash']:,.2f}")

        # Run trading session
        logger.info("\n🔍 Checking trading signals...")
        trader.check_trading_signals()

        logger.info("\n" + "=" * 80)
        logger.info("✅ Daily trading check completed")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ Error in daily trading check: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    run_daily_trade()
