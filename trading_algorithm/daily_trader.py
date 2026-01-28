#!/usr/bin/env python3
"""Daily trading script - runs once per day at market open."""

import os
import logging
from datetime import datetime, timedelta
import pytz
import json
from .live_trader import AlpacaLiveTrader
from .dynamodb_handler import DynamoDBHandler

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


def calculate_entry_price_targets(sma, wma, vix_4d_ago, wma_4d_ago, current_tecl_price=None):
    """Calculate what TECL prices would trigger buy signals."""
    targets = {}

    # Immediate buy threshold
    targets['immediate_buy'] = round(0.75 * sma, 2)

    # VIX condition buy threshold (if VIX condition is met)
    targets['vix_buy_threshold'] = round(1.25 * sma, 2)

    # Is VIX condition currently met? (using VIX from 4 days ago)
    if vix_4d_ago is not None and wma_4d_ago is not None:
        vix_condition_met = vix_4d_ago > (1.04 * wma_4d_ago)
        # Convert to native Python bool for JSON serialization
        targets['vix_condition_active'] = bool(vix_condition_met)
        targets['vix_threshold_4d_ago'] = round(1.04 * wma_4d_ago, 2)
        targets['vix_4d_ago'] = round(vix_4d_ago, 2)
    else:
        targets['vix_condition_active'] = False
        targets['vix_threshold_4d_ago'] = None
        targets['vix_4d_ago'] = None

    return targets


def calculate_fund_metrics(db):
    """Calculate fund performance metrics from DynamoDB events."""
    # Get all BUY and SELL events
    buy_events = db.get_recent_events(event_type="BUY", limit=1000)
    sell_events = db.get_recent_events(event_type="SELL", limit=1000)

    # Fund inception date - date of first BUY event
    fund_inception_date = None
    days_active = 0
    total_positions_entered = len(buy_events)
    total_positions_exited = len(sell_events)

    if buy_events:
        # Sort buy events by timestamp to find the first one
        buy_events_sorted = sorted(buy_events, key=lambda x: x.get('timestamp', ''))
        first_buy = buy_events_sorted[0]
        fund_inception_date = first_buy.get('timestamp', '').split('T')[0]  # Get YYYY-MM-DD

        # Calculate days since inception
        if fund_inception_date:
            inception_dt = datetime.fromisoformat(fund_inception_date)
            days_active = (datetime.now() - inception_dt).days

    # Calculate total invested (sum of all BUY transactions)
    total_invested = sum(
        event.get('price', 0) * event.get('quantity', 0)
        for event in buy_events
    )

    # Calculate total received from sales (sum of all SELL transactions)
    total_received = sum(
        event.get('price', 0) * event.get('quantity', 0)
        for event in sell_events
    )

    # Get initial capital from state
    state = db.load_state(trader_id="main")
    initial_capital = state.get('initial_capital')

    return {
        'fund_inception_date': fund_inception_date,
        'days_active': days_active,
        'total_positions_entered': total_positions_entered,
        'total_positions_exited': total_positions_exited,
        'total_invested': total_invested,
        'total_received': total_received,
        'initial_capital': initial_capital,
    }


def generate_daily_report(trader, entered_today, exited_today):
    """Generate a comprehensive daily trading report."""
    et_tz = pytz.timezone('US/Eastern')
    now_et = datetime.now(et_tz)

    # Get fund performance metrics from DynamoDB
    db = DynamoDBHandler()
    fund_metrics = calculate_fund_metrics(db)

    report = {
        'date': now_et.strftime('%Y-%m-%d'),
        'time': now_et.strftime('%I:%M %p ET'),
        'entered_position_today': bool(entered_today),
        'exited_position_today': bool(exited_today),
        'currently_in_position': bool(trader.in_position),
        'days_since_last_trade': None,
        'exit_price_needed': None,
        'current_tecl_price': None,
        'current_vix': None,
        'sma_tecl': None,
        'wma_vix': None,
        'entry_targets': None,
        'vix_history': None,
        'position_entry_date': None,
        'position_entry_size': None,
        'position_entry_price': None,
        'position_gain_loss_pct': None,
        'position_gain_loss_dollars': None,
        'position_current_value': None,
        # Fund performance metrics
        'fund_inception_date': fund_metrics['fund_inception_date'] or 'Not Started',
        'fund_days_active': fund_metrics['days_active'],
        'total_positions_entered': fund_metrics['total_positions_entered'],
        'total_positions_exited': fund_metrics['total_positions_exited'],
        'total_invested': fund_metrics['total_invested'],
        'total_received': fund_metrics['total_received'],
        'initial_capital': fund_metrics['initial_capital'],
        'current_balance': None,
        'total_returns_pct': None,
        'annualized_returns_pct': None,
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

            # Get VIX history (last 5 days)
            if len(merged_df) >= 5:
                vix_history = []
                for i in range(5, 0, -1):
                    vix_history.append(round(merged_df.iloc[-i]['OPEN_vix'], 2))
                report['vix_history'] = vix_history

            # Calculate entry price targets
            if report['sma_tecl'] and report['wma_vix']:
                # Get VIX and WMA from 4 days ago for the condition check
                vix_4d_ago = None
                wma_4d_ago = None
                if len(merged_df) >= 5:
                    vix_4d_ago = merged_df.iloc[-5]['OPEN_vix']
                    wma_4d_ago = merged_df.iloc[-5]['WMA_vix']

                report['entry_targets'] = calculate_entry_price_targets(
                    report['sma_tecl'],
                    report['wma_vix'],
                    vix_4d_ago,
                    wma_4d_ago,
                    report['current_tecl_price']
                )

    # Position info
    if trader.in_position and trader.purchase_price:
        report['exit_price_needed'] = round(trader.purchase_price * 1.058, 2)
        report['purchase_price'] = round(trader.purchase_price, 2)
        report['position_size'] = trader.position_size

        # Position tracking details
        if trader.purchase_date:
            report['position_entry_date'] = trader.purchase_date.strftime('%b %d, %Y')
        report['position_entry_price'] = round(trader.purchase_price, 2)
        report['position_entry_size'] = trader.position_size

        # Calculate current position value and gain/loss
        if report['current_tecl_price']:
            current_value = report['current_tecl_price'] * trader.position_size
            entry_value = trader.purchase_price * trader.position_size
            gain_loss_dollars = current_value - entry_value
            gain_loss_pct = ((report['current_tecl_price'] / trader.purchase_price) - 1) * 100

            report['position_current_value'] = round(current_value, 2)
            report['position_gain_loss_dollars'] = round(gain_loss_dollars, 2)
            report['position_gain_loss_pct'] = round(gain_loss_pct, 2)

    # Days since last trade
    if trader.last_sell_date:
        days_since = (now_et.date() - trader.last_sell_date).days
        report['days_since_last_trade'] = days_since

    # Get account info for current balance and returns calculation
    account_info = trader.get_account_info()
    report['current_balance'] = account_info['portfolio_value']

    # Calculate returns based on initial capital vs current balance
    if report['initial_capital']:
        initial_capital = report['initial_capital']
        current_balance = report['current_balance']

        # Total returns percentage: (current - initial) / initial
        total_returns = ((current_balance - initial_capital) / initial_capital) * 100
        report['total_returns_pct'] = round(total_returns, 2)

        # Annualized returns (only if fund has been active for at least 1 day)
        if report['fund_days_active'] > 0:
            years_active = report['fund_days_active'] / 365.25
            # Annualized return = ((current / initial) ^ (1 / years)) - 1
            annualized_returns = (((current_balance / initial_capital) ** (1 / years_active)) - 1) * 100
            report['annualized_returns_pct'] = round(annualized_returns, 2)
        else:
            report['annualized_returns_pct'] = 0.0
    else:
        # Fallback if initial_capital not set (shouldn't happen after migration)
        report['total_returns_pct'] = 0.0
        report['annualized_returns_pct'] = 0.0

    return report


def format_number(value):
    """Format numbers with commas for values > 9999."""
    if value is None:
        return 'N/A'
    if abs(value) > 9999:
        return f"{value:,.2f}"
    return f"{value:.2f}"


def format_report_text(report):
    """Format the report as readable text."""
    lines = []
    lines.append("=" * 60)
    lines.append(f"DAILY TRADING REPORT - {report['date']} {report['time']}")
    lines.append("=" * 60)
    lines.append("")

    # Fund Performance Summary
    lines.append("FUND PERFORMANCE:")
    lines.append(f"   Date of fund inception: {report['fund_inception_date']}")
    lines.append(f"   Days fund has been active: {report['fund_days_active']} Days")
    lines.append(f"   Total number of positions entered: {report['total_positions_entered']}")
    lines.append(f"   Total number of positions exited: {report['total_positions_exited']}")
    if report['initial_capital']:
        lines.append(f"   Initial capital: ${format_number(report['initial_capital'])}")
    lines.append(f"   Current balance: ${format_number(report['current_balance'])}")
    lines.append(f"   Total returns: {report['total_returns_pct']}%")
    lines.append(f"   Annualized returns: {report['annualized_returns_pct']}%")
    lines.append("")

    # Trading Activity
    lines.append("TODAY'S ACTIVITY:")
    lines.append(f"   Entered Position Today: {'YES' if report['entered_position_today'] else 'NO'}")
    lines.append(f"   Exited Position Today:  {'YES' if report['exited_position_today'] else 'NO'}")
    lines.append("")

    # Position Status
    lines.append("CURRENT POSITION:")
    if report['currently_in_position']:
        lines.append(f"   Status: IN POSITION")
        if report['position_entry_date']:
            lines.append(f"   Position Entry Date: {report['position_entry_date']}")
        if report['position_entry_size']:
            entry_value = report['position_entry_price'] * report['position_entry_size']
            lines.append(f"   Position Entry Size: ${format_number(entry_value)}")
        if report['position_entry_price']:
            lines.append(f"   Position Entry Price: TECL = ${format_number(report['position_entry_price'])}")
        if report['position_gain_loss_pct'] is not None and report['position_current_value']:
            gain_loss_sign = '+' if report['position_gain_loss_pct'] >= 0 else ''
            lines.append(f"   Position Gain (Loss): {gain_loss_sign}{report['position_gain_loss_pct']:.1f}%, ${format_number(report['position_current_value'])}")
        if report['exit_price_needed']:
            lines.append(f"   Price Needed for Exit: TECL = ${format_number(report['exit_price_needed'])}")
    else:
        lines.append(f"   Status: NO POSITION")
        if report['days_since_last_trade'] is not None:
            lines.append(f"   Days Since Last Trade: {report['days_since_last_trade']}")
    lines.append("")

    # Market Data
    lines.append("CURRENT MARKET DATA:")
    if report['current_tecl_price']:
        lines.append(f"   TECL Price: ${format_number(report['current_tecl_price'])}")
    else:
        lines.append("   TECL Price: N/A")
    lines.append(f"   VIX: {report['vix_history'][4]}")
    if report['sma_tecl']:
        lines.append(f"   TECL 30-day SMA: ${format_number(report['sma_tecl'])}")
    else:
        lines.append("   TECL 30-day SMA: N/A")
    lines.append(f"   VIX 30-day WMA: {report['wma_vix'] or 'N/A'}")
    lines.append("")

    # VIX History
    if report['vix_history']:
        lines.append("VIX HISTORY:")
        vix_hist = report['vix_history']
        lines.append(f"   VIX 4 days ago: {vix_hist[0]}")
        lines.append(f"   VIX 3 days ago: {vix_hist[1]}")
        lines.append(f"   VIX 2 days ago: {vix_hist[2]}")
        lines.append(f"   VIX 1 day ago: {vix_hist[3]}")
        lines.append(f"   VIX today: {vix_hist[4]}")
        lines.append("")

    # Entry Targets
    if report['entry_targets']:
        lines.append("ENTRY PRICE TARGETS:")
        targets = report['entry_targets']
        lines.append(f"   Immediate Buy if TECL < ${format_number(targets['immediate_buy'])}")
        lines.append(f"   VIX Buy Threshold: TECL < ${format_number(targets['vix_buy_threshold'])}")

        vix_status = "MET" if targets['vix_condition_active'] else "NOT MET"
        if targets['vix_4d_ago'] is not None and targets['vix_threshold_4d_ago'] is not None:
            lines.append(f"   VIX Condition (VIX 4 days ago > ${targets['vix_threshold_4d_ago']}): {vix_status}")
            lines.append(f"      VIX 4 days ago: {targets['vix_4d_ago']}")
        else:
            lines.append("   VIX Condition: INSUFFICIENT DATA (need 5+ days)")

        if report['current_tecl_price']:
            distance_to_buy = report['current_tecl_price'] - targets['immediate_buy']
            distance_pct = (distance_to_buy / report['current_tecl_price'] * 100)
            # Make it clear which direction: "TECL falls $X" means price needs to drop
            lines.append(f"   Distance to Immediate Buy: TECL falls ${format_number(distance_to_buy)} ({distance_pct:.1f}%)")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)


def run_daily_trade():
    """Execute the daily trading check at market open."""
    et_tz = pytz.timezone('US/Eastern')
    now_et = datetime.now(et_tz)

    logger.info("=" * 80)
    logger.info(f"DAILY TRADING CHECK - {now_et.strftime('%Y-%m-%d %I:%M %p ET')}")
    logger.info("=" * 80)

    # Skip weekends
    if now_et.weekday() >= 5:
        logger.info("Weekend detected - market is closed")
        return

    entered_today = False
    exited_today = False

    try:
        trader = AlpacaLiveTrader()

        # Check if market is open
        clock = trader.trading_client.get_clock()
        if not clock.is_open:
            logger.info("Market is currently closed")
            logger.info(f"Next market open: {clock.next_open}")
            return

        # Get account info
        account_info = trader.get_account_info()
        logger.info(f"Account Portfolio Value: ${account_info['portfolio_value']:,.2f}")
        logger.info(f"Available Buying Power: ${account_info['buying_power']:,.2f}")
        logger.info(f"Cash: ${account_info['cash']:,.2f}")

        # Track position before trading
        was_in_position = trader.in_position

        # Run trading session
        logger.info("\nChecking trading signals...")
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

        # Log daily report event to DynamoDB
        db = DynamoDBHandler()
        db.log_event(
            event_type="DAILY_REPORT",
            symbol="TECL",
            price=report.get('current_tecl_price'),
            vix=report.get('current_vix'),
            sma_tecl=report.get('sma_tecl'),
            wma_vix=report.get('wma_vix'),
            details={
                "entered_position_today": entered_today,
                "exited_position_today": exited_today,
                "currently_in_position": report.get('currently_in_position'),
                "entry_targets": report.get('entry_targets'),
                "portfolio_value": account_info['portfolio_value'],
                "buying_power": account_info['buying_power'],
                "position_gain_loss_pct": report.get('position_gain_loss_pct'),
                "position_gain_loss_dollars": report.get('position_gain_loss_dollars')
            }
        )

        logger.info("\n" + "=" * 80)
        logger.info("Daily trading check completed")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"Error in daily trading check: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    run_daily_trade()
