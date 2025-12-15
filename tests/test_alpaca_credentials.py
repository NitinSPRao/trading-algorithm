#!/usr/bin/env python3
"""Test Alpaca API credentials."""

import os
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient

# Load environment variables
load_dotenv()

def test_alpaca_credentials():
    """Test Alpaca API credentials and connection."""
    print("🔑 Testing Alpaca API Credentials")
    print("=" * 40)
    
    # Check if credentials are set
    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')
    base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets/v2')
    
    print(f"API Key: {api_key[:8] + '...' if api_key else 'NOT SET'}")
    print(f"Secret Key: {'SET' if secret_key else 'NOT SET'}")
    print(f"Base URL: {base_url}")
    
    if not api_key or not secret_key:
        print("❌ Credentials not found in .env file")
        return False
    
    print("\n🔍 Testing connection...")
    
    try:
        # Initialize trading client
        trading_client = TradingClient(api_key, secret_key, paper=True)
        
        # Test 1: Get account info
        print("   Testing account access...")
        account = trading_client.get_account()
        
        print(f"✅ Account connected successfully!")
        print(f"   Account ID: {account.id}")
        print(f"   Status: {account.status}")
        print(f"   Portfolio Value: ${float(account.portfolio_value):,.2f}")
        print(f"   Buying Power: ${float(account.buying_power):,.2f}")
        print(f"   Cash: ${float(account.cash):,.2f}")
        
        # Test 2: Check if market is open
        print("\n   Testing market status...")
        clock = trading_client.get_clock()
        
        print(f"   Market Open: {clock.is_open}")
        print(f"   Next Open: {clock.next_open}")
        print(f"   Next Close: {clock.next_close}")
        
        # Test 3: Get positions (if any)
        print("\n   Testing positions...")
        positions = trading_client.get_all_positions()
        
        if positions:
            print(f"   Current positions: {len(positions)}")
            for pos in positions:
                print(f"   - {pos.symbol}: {pos.qty} shares")
        else:
            print("   No current positions")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        
        # Check for specific error types
        error_str = str(e).lower()
        if '401' in error_str or 'unauthorized' in error_str:
            print("💡 This is an authentication error - check your API credentials")
        elif '403' in error_str or 'forbidden' in error_str:
            print("💡 This is a permissions error - make sure you're using paper trading keys")
        elif 'timeout' in error_str:
            print("💡 This is a network error - check your internet connection")
        
        return False

if __name__ == "__main__":
    success = test_alpaca_credentials()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 Alpaca credentials are working!")
        print("✅ Ready for live trading")
    else:
        print("❌ Alpaca credential test failed")
        print("📝 Double-check your API keys in .env file")