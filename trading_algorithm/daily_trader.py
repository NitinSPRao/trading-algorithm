#!/usr/bin/env python3
"""Daily trading script - runs once per day at market open."""

import os
import logging
from datetime import datetime, timedelta
import pytz
import json
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


def calculate_entry_price_targets(sma, wma, vix):
    """Calculate what TECL prices would trigger buy signals."""
    targets = {}

    # Immediate buy threshold
    targets['immediate_buy'] = round(0.75 * sma, 2)

    # VIX condition buy threshold (if VIX condition is met)
    targets['vix_buy_threshold'] = round(1.25 * sma, 2)

    # Is VIX condition currently met?
    vix_condition_met = vix > (1.04 * wma)
    targets['vix_condition_active'] = vix_condition_met
    targets['vix_threshold'] = round(1.04 * wma, 2)

    return targets


def generate_daily_report(trader, entered_today, exited_today):
    """Generate a comprehensive daily trading report."""
    et_tz = pytz.timezone('US/Eastern')
    now_et = datetime.now(et_tz)

    report = {
        'date': now_et.strftime('%Y-%m-%d'),
        'time': now_et.strftime('%I:%M %p ET'),
        'entered_position_today': entered_today,
        'exited_position_today': exited_today,
        'currently_in_position': trader.in_position,
        'days_since_last_trade': None,
        'exit_price_needed': None,
        'current_tecl_price': None,
        'current_vix': None,
        'sma_tecl': None,
        'wma_vix': None,
        'entry_targets': None
    }

    # Get current prices and indicators
    tecl_price = trader.get_current_price('TECL')
    vix_price = trader.get_current_price('VIX')

    if tecl_price:
        report['current_tecl_price'] = round(tecl_price, 2)
    if vix_price:
        report['current_vix'] = round(vix_price, 2)

    # Get historical data for indicators
    tecl_data = trader.get_historical_data('TECL')
    vix_data = trader.get_historical_data('VIX')

    if not tecl_data.empty and not vix_data.empty:
        # Calculate indicators
        from .backtesting import calculate_indicators
        import pandas as pd

        tecl_data = tecl_data.rename(columns={'Open': 'Open_tecl'})
        vix_data = vix_data.rename(columns={'Open': 'OPEN_vix'})

        if tecl_data.index.tz is not None:
            tecl_data.index = tecl_data.index.tz_localize(None)
        if vix_data.index.tz is not None:
            vix_data.index = vix_data.index.tz_localize(None)

        merged_df = pd.merge(tecl_data[['Open_tecl']], vix_data[['OPEN_vix']],
                           left_index=True, right_index=True, how='inner')

        if len(merged_df) >= 30:
            merged_df = calculate_indicators(merged_df)
            latest = merged_df.iloc[-1]

            report['sma_tecl'] = round(latest['SMA_tecl'], 2)
            report['wma_vix'] = round(latest['WMA_vix'], 2)

            # Calculate entry price targets
            if report['current_vix'] and report['sma_tecl'] and report['wma_vix']:
                report['entry_targets'] = calculate_entry_price_targets(
                    report['sma_tecl'],
                    report['wma_vix'],
                    report['current_vix']
                )

    # Position info
    if trader.in_position and trader.purchase_price:
        report['exit_price_needed'] = round(trader.purchase_price * 1.058, 2)
        report['purchase_price'] = round(trader.purchase_price, 2)
        report['position_size'] = trader.position_size

    # Days since last trade
    if trader.last_sell_date:
        days_since = (now_et.date() - trader.last_sell_date).days
        report['days_since_last_trade'] = days_since

    return report


def format_report_text(report):
    """Format the report as readable text."""
    lines = []
    lines.append("=" * 60)
    lines.append(f"📊 DAILY TRADING REPORT - {report['date']} {report['time']}")
    lines.append("=" * 60)
    lines.append("")

    # Trading Activity
    lines.append("🔄 TODAY'S ACTIVITY:")
    lines.append(f"   Entered Position Today: {'✅ YES' if report['entered_position_today'] else '❌ NO'}")
    lines.append(f"   Exited Position Today:  {'✅ YES' if report['exited_position_today'] else '❌ NO'}")
    lines.append("")

    # Position Status
    lines.append("📍 CURRENT POSITION:")
    if report['currently_in_position']:
        lines.append(f"   Status: 🟢 IN POSITION")
        lines.append(f"   Purchase Price: ${report.get('purchase_price', 'N/A')}")
        lines.append(f"   Position Size: {report.get('position_size', 'N/A')} shares")
        lines.append(f"   Exit Price Needed: ${report['exit_price_needed']}")
        if report['current_tecl_price']:
            profit_pct = ((report['current_tecl_price'] / report['purchase_price']) - 1) * 100
            lines.append(f"   Current Profit: {profit_pct:+.2f}%")
    else:
        lines.append(f"   Status: ⚪ NO POSITION")
        if report['days_since_last_trade'] is not None:
            lines.append(f"   Days Since Last Trade: {report['days_since_last_trade']}")
    lines.append("")

    # Market Data
    lines.append("📈 CURRENT MARKET DATA:")
    lines.append(f"   TECL Price: ${report['current_tecl_price'] or 'N/A'}")
    lines.append(f"   VIX: {report['current_vix'] or 'N/A'}")
    lines.append(f"   TECL 30-day SMA: ${report['sma_tecl'] or 'N/A'}")
    lines.append(f"   VIX 30-day WMA: {report['wma_vix'] or 'N/A'}")
    lines.append("")

    # Entry Targets
    if report['entry_targets']:
        lines.append("🎯 ENTRY PRICE TARGETS:")
        targets = report['entry_targets']
        lines.append(f"   Immediate Buy if TECL < ${targets['immediate_buy']}")
        lines.append(f"   VIX Buy Threshold: TECL < ${targets['vix_buy_threshold']}")

        vix_status = "✅ MET" if targets['vix_condition_active'] else "❌ NOT MET"
        lines.append(f"   VIX Condition (VIX > ${targets['vix_threshold']}): {vix_status}")

        if report['current_tecl_price']:
            distance_to_buy = report['current_tecl_price'] - targets['immediate_buy']
            lines.append(f"   Distance to Immediate Buy: ${distance_to_buy:.2f} ({(distance_to_buy/report['current_tecl_price']*100):.1f}%)")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)


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

    entered_today = False
    exited_today = False

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

        # Track position before trading
        was_in_position = trader.in_position

        # Run trading session
        logger.info("\n🔍 Checking trading signals...")
        trader.check_trading_signals()

        # Track position after trading
        is_in_position = trader.in_position

        # Determine if trades occurred
        if not was_in_position and is_in_position:
            entered_today = True
        elif was_in_position and not is_in_position:
            exited_today = True

        # Generate daily report
        report = generate_daily_report(trader, entered_today, exited_today)
        report_text = format_report_text(report)

        # Log the report
        logger.info("\n" + report_text)

        # Save report as JSON for GitHub Actions to parse
        report_file = os.path.join(log_dir, 'daily_report.json')
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        # Also save formatted text version
        report_text_file = os.path.join(log_dir, 'daily_report.txt')
        with open(report_text_file, 'w') as f:
            f.write(report_text)

        logger.info("\n" + "=" * 80)
        logger.info("✅ Daily trading check completed")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ Error in daily trading check: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    run_daily_trade()
