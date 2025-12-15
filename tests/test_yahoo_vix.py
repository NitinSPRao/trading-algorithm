#!/usr/bin/env python3
"""Test Yahoo Finance for VIX data availability."""

import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd

def test_yahoo_vix():
    """Test Yahoo Finance VIX data access."""
    print("🔑 Testing Yahoo Finance (no API key required)")
    
    # Test different VIX symbols for Yahoo Finance
    vix_symbols = [
        '^VIX',    # Most common VIX symbol on Yahoo
        'VIX',     # Alternative
        '^VXX',    # VIX ETF
        'VIXM24.CBE'  # VIX futures
    ]
    
    for symbol in vix_symbols:
        print(f"\n📊 Testing symbol: {symbol}")
        
        try:
            # Create ticker object
            ticker = yf.Ticker(symbol)
            
            # Test 1: Current info and recent price
            print("   🔍 Testing current info...")
            info = ticker.info
            
            if info and 'regularMarketPrice' in info:
                current_price = info['regularMarketPrice']
                prev_close = info.get('previousClose', 'N/A')
                print(f"   ✅ Current price: ${current_price:.2f}")
                print(f"   📈 Previous close: ${prev_close}")
            
            # Test 2: Recent historical data (last 5 days)
            print("   🔍 Testing recent historical data...")
            recent_data = ticker.history(period='5d')
            
            if not recent_data.empty:
                latest_date = recent_data.index[-1].strftime('%Y-%m-%d')
                latest_open = recent_data['Open'].iloc[-1]
                latest_close = recent_data['Close'].iloc[-1]
                
                print(f"   ✅ Recent data: {len(recent_data)} days")
                print(f"   📅 Latest: {latest_date}")
                print(f"   💰 Open: ${latest_open:.2f}, Close: ${latest_close:.2f}")
            
            # Test 3: Extended historical data (for 30-day indicators)
            print("   🔍 Testing extended historical data...")
            historical_data = ticker.history(period='60d')
            
            if not historical_data.empty and len(historical_data) >= 30:
                print(f"   ✅ Historical data: {len(historical_data)} days")
                print(f"   📊 Date range: {historical_data.index[0].strftime('%Y-%m-%d')} to {historical_data.index[-1].strftime('%Y-%m-%d')}")
                
                # Test calculating moving average (like in your strategy)
                test_moving_average(historical_data, symbol)
                return True
            else:
                print(f"   ⚠️  Only {len(historical_data) if not historical_data.empty else 0} days of data")
                
        except Exception as e:
            print(f"   ❌ Error testing {symbol}: {e}")
    
    return False

def test_moving_average(data, symbol):
    """Test calculating 30-day weighted moving average like in your strategy."""
    print("   🔍 Testing moving average calculation...")
    
    try:
        # Calculate 30-day WMA like in your backtesting code
        import numpy as np
        
        weights = np.arange(1, 31)
        wma = data['Open'].rolling(window=30, min_periods=30).apply(
            lambda x: np.dot(x, weights) / weights.sum(), raw=True
        )
        
        # Get latest valid WMA value
        latest_wma = wma.dropna().iloc[-1] if not wma.dropna().empty else None
        latest_open = data['Open'].iloc[-1]
        
        if latest_wma:
            print(f"   ✅ WMA calculation works!")
            print(f"   📊 Latest Open: ${latest_open:.2f}")
            print(f"   📊 Latest 30-day WMA: ${latest_wma:.2f}")
            print(f"   🎯 Signal check: VIX > 1.04 * WMA? {latest_open > 1.04 * latest_wma}")
            return True
        else:
            print(f"   ❌ Could not calculate WMA")
            
    except Exception as e:
        print(f"   ❌ WMA calculation error: {e}")
    
    return False

def test_live_data_frequency():
    """Test how frequently Yahoo Finance updates VIX data."""
    print(f"\n⏱️  Testing data freshness...")
    
    try:
        vix = yf.Ticker('^VIX')
        
        # Get very recent data
        recent = vix.history(period='1d', interval='1m')
        
        if not recent.empty:
            latest_time = recent.index[-1]
            now = datetime.now()
            age_minutes = (now - latest_time.replace(tzinfo=None)).total_seconds() / 60
            
            print(f"   📅 Latest data: {latest_time}")
            print(f"   ⏰ Data age: {age_minutes:.1f} minutes")
            
            if age_minutes < 60:
                print(f"   ✅ Data is fresh (< 1 hour old)")
            else:
                print(f"   ⚠️  Data is {age_minutes/60:.1f} hours old")
        
    except Exception as e:
        print(f"   ℹ️  Minute-level data not available: {e}")
        print(f"   💡 Daily data should be sufficient for your strategy")

if __name__ == "__main__":
    print("🧪 Testing Yahoo Finance VIX Data Access")
    print("=" * 45)
    
    success = test_yahoo_vix()
    test_live_data_frequency()
    
    print("\n" + "=" * 45)
    if success:
        print("🎉 SUCCESS: Yahoo Finance can provide VIX data!")
        print("💡 No API key required - ready to integrate!")
        print("⚡ Free, reliable, and perfect for your strategy")
        print("🔄 Updates daily (sufficient for your trading logic)")
    else:
        print("😞 FAILED: Issues with Yahoo Finance VIX data")
        print("🤔 This would be unusual - Yahoo Finance is very reliable")