#!/usr/bin/env python3
"""View DynamoDB data for trading algorithm."""

import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv
from trading_algorithm.dynamodb_handler import DynamoDBHandler

# Load environment variables
load_dotenv()


def view_state():
    """View current trading state."""
    db = DynamoDBHandler()
    state = db.load_state(trader_id="main")

    print("=" * 80)
    print("CURRENT TRADING STATE")
    print("=" * 80)

    if not state:
        print("No state found in DynamoDB")
        return

    print(f"In Position: {state.get('in_position')}")
    if state.get('in_position'):
        print(f"Purchase Price: ${state.get('purchase_price', 0):.2f}")
        print(f"Purchase Date: {state.get('purchase_date')}")
        print(f"Position Size: {state.get('position_size')} shares")
    else:
        print("Currently not holding any position")

    if state.get('last_sell_date'):
        print(f"Last Sell Date: {state.get('last_sell_date')}")

    print(f"Last Updated: {state.get('last_updated')}")
    print()


def view_events(days=7, event_type=None, limit=50):
    """View recent trading events."""
    db = DynamoDBHandler()

    print("=" * 80)
    print(f"TRADING EVENTS (Last {days} days)")
    if event_type:
        print(f"Filtered by: {event_type}")
    print("=" * 80)

    # Get events for each day
    all_events = []
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        events = db.get_events(event_date=date)
        all_events.extend(events)

    # Filter by event type if specified
    if event_type:
        all_events = [e for e in all_events if e.get('event_type') == event_type]

    # Sort by timestamp descending
    all_events.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

    # Limit results
    all_events = all_events[:limit]

    if not all_events:
        print("No events found")
        return

    print(f"Found {len(all_events)} events\n")

    for i, event in enumerate(all_events, 1):
        timestamp = event.get('timestamp', '')
        event_type = event.get('event_type', '')
        symbol = event.get('symbol', '')
        price = event.get('price')
        quantity = event.get('quantity')

        print(f"{i}. [{timestamp}] {event_type} - {symbol}")

        if price is not None:
            print(f"   Price: ${price:.2f}", end="")
            if quantity is not None:
                print(f" x {quantity} shares", end="")
            print()

        if event.get('vix') is not None:
            print(f"   VIX: {event['vix']:.2f}", end="")
        if event.get('sma_tecl') is not None:
            print(f"  SMA: ${event['sma_tecl']:.2f}", end="")
        if event.get('wma_vix') is not None:
            print(f"  WMA: {event['wma_vix']:.2f}", end="")

        if event.get('vix') or event.get('sma_tecl') or event.get('wma_vix'):
            print()

        # Show details for specific event types
        details = event.get('details', {})
        if event_type == 'BUY' and details:
            if 'reason' in details:
                print(f"   Reason: {details['reason']}")

        elif event_type == 'SELL' and details:
            if 'profit_pct' in details:
                print(f"   Profit: {details['profit_pct']:.2f}% (${details.get('profit_dollars', 0):.2f})")
            if 'hold_days' in details:
                print(f"   Held: {details['hold_days']} days")

        elif event_type == 'DAILY_REPORT' and details:
            if 'entered_position_today' in details:
                print(f"   Entered: {details['entered_position_today']}, Exited: {details['exited_position_today']}")
            if 'portfolio_value' in details:
                print(f"   Portfolio: ${details['portfolio_value']:,.2f}")

        print()


def main():
    parser = argparse.ArgumentParser(description='View DynamoDB trading data')
    parser.add_argument('command', choices=['state', 'events'], help='What to view')
    parser.add_argument('--days', type=int, default=7, help='Number of days to look back (for events)')
    parser.add_argument('--type', choices=['BUY', 'SELL', 'SIGNAL_CHECK', 'DAILY_REPORT'],
                        help='Filter events by type')
    parser.add_argument('--limit', type=int, default=50, help='Maximum number of events to show')

    args = parser.parse_args()

    if args.command == 'state':
        view_state()
    elif args.command == 'events':
        view_events(days=args.days, event_type=args.type, limit=args.limit)


if __name__ == "__main__":
    main()
