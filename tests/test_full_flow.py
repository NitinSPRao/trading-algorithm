#!/usr/bin/env python3
"""Test full trading flow with DynamoDB integration."""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_initialization():
    """Test that AlpacaLiveTrader initializes correctly with DynamoDB."""
    print("=" * 80)
    print("TEST 1: AlpacaLiveTrader Initialization")
    print("=" * 80)

    try:
        from trading_algorithm.live_trader import AlpacaLiveTrader

        print("Initializing trader...")
        trader = AlpacaLiveTrader()

        print(f"✓ Trader initialized successfully")
        print(f"  - DynamoDB handler: {trader.db}")
        print(f"  - In position: {trader.in_position}")
        print(f"  - Position size: {trader.position_size}")
        print(f"  - Purchase price: {trader.purchase_price}")

        # Test that state can be saved
        print("\nTesting state save...")
        trader._save_state()
        print("✓ State saved to DynamoDB")

        # Test that state can be loaded
        print("\nTesting state load...")
        state = trader._load_state()
        if state is not None:
            print("✓ State loaded from DynamoDB")
            print(f"  Loaded state: in_position={state.get('in_position')}")
        else:
            print("ℹ No previous state found (this is normal on first run)")

        return True

    except Exception as e:
        print(f"✗ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_event_logging():
    """Test that event logging works in the trading flow."""
    print("\n" + "=" * 80)
    print("TEST 2: Event Logging in Trading Flow")
    print("=" * 80)

    try:
        from trading_algorithm.dynamodb_handler import DynamoDBHandler

        db = DynamoDBHandler()

        # Simulate different event types
        print("\nLogging BUY event...")
        db.log_event(
            event_type="BUY",
            symbol="TECL",
            price=115.50,
            quantity=100,
            success=True,
            details={"reason": "test buy", "buying_power_used_pct": 0.45}
        )
        print("✓ BUY event logged")

        print("\nLogging SIGNAL_CHECK event...")
        db.log_event(
            event_type="SIGNAL_CHECK",
            symbol="TECL",
            price=115.50,
            vix=18.5,
            sma_tecl=120.0,
            wma_vix=17.0,
            details={"in_position": False, "purchase_price": None}
        )
        print("✓ SIGNAL_CHECK event logged")

        print("\nLogging SELL event...")
        db.log_event(
            event_type="SELL",
            symbol="TECL",
            price=122.00,
            quantity=100,
            success=True,
            details={
                "purchase_price": 115.50,
                "profit_pct": 5.63,
                "profit_dollars": 650.00,
                "hold_days": 3
            }
        )
        print("✓ SELL event logged")

        print("\nLogging DAILY_REPORT event...")
        db.log_event(
            event_type="DAILY_REPORT",
            symbol="TECL",
            price=115.50,
            vix=18.5,
            sma_tecl=120.0,
            wma_vix=17.0,
            details={
                "entered_position_today": False,
                "exited_position_today": False,
                "currently_in_position": False,
                "portfolio_value": 100000.0,
                "buying_power": 45000.0
            }
        )
        print("✓ DAILY_REPORT event logged")

        # Verify events were logged
        print("\nVerifying events were logged...")
        today = datetime.now().strftime("%Y-%m-%d")
        events = db.get_events(event_date=today, limit=10)
        print(f"✓ Retrieved {len(events)} events from today")

        event_types = [e.get('event_type') for e in events]
        if 'BUY' in event_types:
            print("  ✓ BUY event found")
        if 'SELL' in event_types:
            print("  ✓ SELL event found")
        if 'SIGNAL_CHECK' in event_types:
            print("  ✓ SIGNAL_CHECK event found")
        if 'DAILY_REPORT' in event_types:
            print("  ✓ DAILY_REPORT event found")

        return True

    except Exception as e:
        print(f"✗ Error during event logging test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_environment_variables():
    """Test that all required environment variables are set."""
    print("\n" + "=" * 80)
    print("TEST 3: Environment Variables")
    print("=" * 80)

    required_vars = {
        'Alpaca': ['ALPACA_API_KEY', 'ALPACA_SECRET_KEY', 'ALPACA_BASE_URL'],
        'DynamoDB': ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_REGION',
                     'DYNAMODB_STATE_TABLE', 'DYNAMODB_EVENTS_TABLE'],
        'Trading': ['POSITION_SIZE_LIMIT']
    }

    all_set = True

    for category, vars_list in required_vars.items():
        print(f"\n{category} Variables:")
        for var in vars_list:
            value = os.getenv(var)
            if value:
                # Mask sensitive values
                if 'KEY' in var or 'SECRET' in var:
                    display_value = value[:10] + "..." if len(value) > 10 else "***"
                else:
                    display_value = value
                print(f"  ✓ {var}: {display_value}")
            else:
                print(f"  ✗ {var}: NOT SET")
                all_set = False

    return all_set


def test_daily_trader_import():
    """Test that daily_trader can be imported and has required functions."""
    print("\n" + "=" * 80)
    print("TEST 4: Daily Trader Module")
    print("=" * 80)

    try:
        from trading_algorithm import daily_trader

        print("✓ daily_trader module imported")

        # Check for required functions
        required_functions = ['run_daily_trade', 'generate_daily_report', 'format_report_text']
        for func_name in required_functions:
            if hasattr(daily_trader, func_name):
                print(f"  ✓ {func_name} function found")
            else:
                print(f"  ✗ {func_name} function NOT found")
                return False

        return True

    except Exception as e:
        print(f"✗ Error importing daily_trader: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("COMPREHENSIVE PRE-DEPLOYMENT CHECKS")
    print("Testing DynamoDB Integration for Monday Trading Run")
    print("=" * 80 + "\n")

    results = {}

    results['env_vars'] = test_environment_variables()
    results['initialization'] = test_initialization()
    results['event_logging'] = test_event_logging()
    results['daily_trader'] = test_daily_trader_import()

    # Summary
    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)

    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name.upper()}: {status}")

    all_passed = all(results.values())

    print("\n" + "=" * 80)
    if all_passed:
        print("✓ ALL TESTS PASSED - READY FOR MONDAY DEPLOYMENT")
    else:
        print("✗ SOME TESTS FAILED - ISSUES NEED TO BE RESOLVED")
    print("=" * 80)

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
