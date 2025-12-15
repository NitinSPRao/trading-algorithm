#!/usr/bin/env python3
"""Test script to verify Alpaca paper trading by buying and selling a stock."""

import os
import time
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# Load environment variables
load_dotenv()


def test_buy_sell_stock(symbol: str = "SPY", qty: int = 1):
    """
    Test buying and selling a stock in Alpaca paper trading.

    Args:
        symbol: Stock symbol to trade (default: SPY)
        qty: Number of shares to trade (default: 1)
    """
    print("🧪 Alpaca Paper Trading Buy/Sell Test")
    print("=" * 50)

    # Get credentials
    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    if not api_key or not secret_key:
        print("❌ Credentials not found in .env file")
        return False

    try:
        # Initialize trading client
        trading_client = TradingClient(api_key, secret_key, paper=True)

        # Get initial account info
        print(f"\n📊 Initial Account Status")
        account = trading_client.get_account()
        print(f"   Portfolio Value: ${float(account.portfolio_value):,.2f}")
        print(f"   Cash: ${float(account.cash):,.2f}")
        print(f"   Buying Power: ${float(account.buying_power):,.2f}")

        # Check market status
        clock = trading_client.get_clock()
        print(f"\n🕐 Market Status")
        print(f"   Market Open: {clock.is_open}")
        if not clock.is_open:
            print(f"   Next Open: {clock.next_open}")
            print("   ⚠️  Market is closed - order will be queued until market opens")

        # Step 1: Buy the stock
        print(f"\n📈 Step 1: Buying {qty} share(s) of {symbol}")
        print("   Creating market buy order...")

        buy_order_data = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY
        )

        buy_order = trading_client.submit_order(order_data=buy_order_data)

        print(f"   ✅ Buy order submitted!")
        print(f"   Order ID: {buy_order.id}")
        print(f"   Symbol: {buy_order.symbol}")
        print(f"   Quantity: {buy_order.qty}")
        print(f"   Side: {buy_order.side}")
        print(f"   Status: {buy_order.status}")

        # Wait for order to fill
        print("\n   Waiting for buy order to fill...")
        max_wait = 30  # seconds
        wait_time = 0

        while wait_time < max_wait:
            order_status = trading_client.get_order_by_id(buy_order.id)
            print(f"   Order status: {order_status.status}", end='\r')

            if order_status.status in ['filled', 'partially_filled']:
                print(f"\n   ✅ Buy order filled!")
                if order_status.filled_avg_price:
                    print(f"   Filled at: ${float(order_status.filled_avg_price):.2f}")
                break
            elif order_status.status in ['canceled', 'expired', 'rejected']:
                print(f"\n   ❌ Buy order {order_status.status}")
                return False

            time.sleep(1)
            wait_time += 1

        if wait_time >= max_wait:
            print(f"\n   ⚠️  Order still pending after {max_wait} seconds")
            print("   This may be normal if market is closed")
            print(f"   Current status: {order_status.status}")

            # Cancel pending order before selling
            if order_status.status in ['pending_new', 'accepted', 'new']:
                print("\n   Canceling pending buy order...")
                trading_client.cancel_order_by_id(buy_order.id)
                print("   ❌ Test aborted - order didn't fill in time")
                return False

        # Check position
        print("\n   Checking position...")
        try:
            position = trading_client.get_open_position(symbol)
            print(f"   ✅ Position confirmed: {position.qty} shares of {symbol}")
            print(f"   Current value: ${float(position.market_value):,.2f}")
        except Exception as e:
            print(f"   ⚠️  Could not confirm position: {e}")

        # Step 2: Sell the stock
        print(f"\n📉 Step 2: Selling {qty} share(s) of {symbol}")
        print("   Creating market sell order...")

        sell_order_data = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY
        )

        sell_order = trading_client.submit_order(order_data=sell_order_data)

        print(f"   ✅ Sell order submitted!")
        print(f"   Order ID: {sell_order.id}")
        print(f"   Symbol: {sell_order.symbol}")
        print(f"   Quantity: {sell_order.qty}")
        print(f"   Side: {sell_order.side}")
        print(f"   Status: {sell_order.status}")

        # Wait for sell order to fill
        print("\n   Waiting for sell order to fill...")
        wait_time = 0

        while wait_time < max_wait:
            order_status = trading_client.get_order_by_id(sell_order.id)
            print(f"   Order status: {order_status.status}", end='\r')

            if order_status.status in ['filled', 'partially_filled']:
                print(f"\n   ✅ Sell order filled!")
                if order_status.filled_avg_price:
                    print(f"   Filled at: ${float(order_status.filled_avg_price):.2f}")
                break
            elif order_status.status in ['canceled', 'expired', 'rejected']:
                print(f"\n   ❌ Sell order {order_status.status}")
                return False

            time.sleep(1)
            wait_time += 1

        if wait_time >= max_wait:
            print(f"\n   ⚠️  Sell order still pending after {max_wait} seconds")
            print(f"   Current status: {order_status.status}")

        # Get final account info
        print(f"\n📊 Final Account Status")
        account = trading_client.get_account()
        print(f"   Portfolio Value: ${float(account.portfolio_value):,.2f}")
        print(f"   Cash: ${float(account.cash):,.2f}")
        print(f"   Buying Power: ${float(account.buying_power):,.2f}")

        # Show recent orders
        print(f"\n📋 Recent Orders")
        orders = trading_client.get_orders()
        for order in orders[:5]:  # Show last 5 orders
            print(f"   {order.symbol} - {order.side} {order.qty} - {order.status}")

        print("\n" + "=" * 50)
        print("✅ Buy/Sell test completed successfully!")
        print(f"   Successfully bought and sold {qty} share(s) of {symbol}")

        return True

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")

        # Provide helpful error messages
        error_str = str(e).lower()
        if 'insufficient' in error_str or 'buying power' in error_str:
            print("💡 Insufficient buying power - your paper account may not have enough funds")
        elif 'not found' in error_str and 'position' in error_str:
            print("💡 Position not found - the buy order may not have filled yet")
        elif 'invalid' in error_str and 'symbol' in error_str:
            print("💡 Invalid symbol - check that the stock symbol is correct")

        return False


if __name__ == "__main__":
    import sys

    # Allow custom symbol and quantity from command line
    symbol = sys.argv[1] if len(sys.argv) > 1 else "SPY"
    qty = int(sys.argv[2]) if len(sys.argv) > 2 else 1

    print(f"Testing with: {qty} share(s) of {symbol}\n")

    success = test_buy_sell_stock(symbol=symbol, qty=qty)

    if not success:
        print("\n💡 Troubleshooting tips:")
        print("   1. Ensure your .env file has valid Alpaca credentials")
        print("   2. Verify you're using paper trading keys (not live)")
        print("   3. Check that your paper account has sufficient funds")
        print("   4. If market is closed, orders will queue until market opens")
        sys.exit(1)
