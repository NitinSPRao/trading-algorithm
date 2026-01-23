#!/usr/bin/env python3
"""Test DynamoDB integration."""

import os
from datetime import datetime
from dotenv import load_dotenv
from trading_algorithm.dynamodb_handler import DynamoDBHandler

# Load environment variables
load_dotenv()

def test_dynamodb_connection():
    """Test basic DynamoDB connection and operations."""
    print("=" * 80)
    print("Testing DynamoDB Integration")
    print("=" * 80)
    print()

    # Initialize handler
    print("1. Initializing DynamoDB handler...")
    db = DynamoDBHandler()
    print(f"   ✓ Connected to region: {db.region}")
    print(f"   ✓ State table: {db.state_table_name}")
    print(f"   ✓ Events table: {db.events_table_name}")
    print()

    # Test state save
    print("2. Testing state save...")
    success = db.save_state(
        in_position=True,
        purchase_price=115.50,
        purchase_date=datetime.now().isoformat(),
        position_size=100,
        last_sell_date=None,
        trader_id="test"
    )
    if success:
        print("   ✓ State saved successfully")
    else:
        print("   ✗ Failed to save state")
        return False
    print()

    # Test state load
    print("3. Testing state load...")
    state = db.load_state(trader_id="test")
    if state:
        print("   ✓ State loaded successfully")
        print(f"   - in_position: {state.get('in_position')}")
        print(f"   - purchase_price: ${state.get('purchase_price'):.2f}")
        print(f"   - position_size: {state.get('position_size')}")
    else:
        print("   ✗ Failed to load state")
        return False
    print()

    # Test event logging
    print("4. Testing event logging...")
    success = db.log_event(
        event_type="TEST_EVENT",
        symbol="TECL",
        price=115.50,
        quantity=100,
        vix=18.5,
        sma_tecl=120.0,
        wma_vix=17.0,
        signal_triggered=True,
        success=True,
        details={"test": "This is a test event"}
    )
    if success:
        print("   ✓ Event logged successfully")
    else:
        print("   ✗ Failed to log event")
        return False
    print()

    # Test event retrieval
    print("5. Testing event retrieval...")
    today = datetime.now().strftime("%Y-%m-%d")
    events = db.get_events(event_date=today, limit=10)
    print(f"   ✓ Retrieved {len(events)} events for today")
    if events:
        for i, event in enumerate(events[:3], 1):
            print(f"   Event {i}:")
            print(f"     - Type: {event.get('event_type')}")
            print(f"     - Symbol: {event.get('symbol')}")
            print(f"     - Price: ${event.get('price', 0):.2f}")
            print(f"     - Timestamp: {event.get('timestamp')}")
    print()

    # Clean up test data
    print("6. Cleaning up test state...")
    db.save_state(
        in_position=False,
        purchase_price=None,
        purchase_date=None,
        position_size=0,
        last_sell_date=None,
        trader_id="test"
    )
    print("   ✓ Test state cleaned up")
    print()

    print("=" * 80)
    print("✓ All DynamoDB tests passed!")
    print("=" * 80)
    return True


if __name__ == "__main__":
    try:
        success = test_dynamodb_connection()
        exit(0 if success else 1)
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
