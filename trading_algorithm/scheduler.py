#!/usr/bin/env python3
"""Periodic scheduler for live trading."""

import schedule
import time
import logging
from datetime import datetime
import pytz
from .live_trader import AlpacaLiveTrader

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def is_market_hours():
    """Check if current time is during market hours (9:30 AM - 4:00 PM ET)."""
    et_tz = pytz.timezone('US/Eastern')
    now_et = datetime.now(et_tz)
    
    # Skip weekends
    if now_et.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    
    # Market hours: 9:30 AM - 4:00 PM ET
    market_open = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
    
    return market_open <= now_et <= market_close

def run_trading_check():
    """Run a single trading check if market is open."""
    if not is_market_hours():
        logger.info("⏰ Outside market hours - skipping trading check")
        return
    
    logger.info("🤖 Running scheduled trading check...")
    
    try:
        trader = AlpacaLiveTrader()
        trader.run_trading_session()
        logger.info("✅ Trading check completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Trading check failed: {e}")

def start_scheduler():
    """Start the periodic scheduler."""
    logger.info("🚀 Starting trading algorithm scheduler")
    logger.info("📅 Will check every 30 minutes during market hours")
    logger.info("⏰ Market hours: Monday-Friday, 9:30 AM - 4:00 PM ET")
    
    # Schedule checks every 30 minutes
    schedule.every(30).minutes.do(run_trading_check)
    
    # Initial check
    run_trading_check()
    
    # Keep running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute for scheduled tasks
            
    except KeyboardInterrupt:
        logger.info("🛑 Scheduler stopped by user")
    except Exception as e:
        logger.error(f"💥 Scheduler error: {e}")

if __name__ == "__main__":
    start_scheduler()