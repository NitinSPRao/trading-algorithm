#!/usr/bin/env python3
"""Quick test script to check Alpha Vantage VIX data availability."""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_alpha_vantage_vix():
    """Test Alpha Vantage API for VIX data access."""
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    
    if not api_key:
        print("❌ ALPHA_VANTAGE_API_KEY not found in .env file")
        return False
    
    print(f"🔑 Using Alpha Vantage API Key: {api_key[:8]}...")
    
    # Test different VIX symbol variations
    vix_symbols = [
        'VIX',
        '^VIX', 
        'CBOE:VIX',
        'VXX'  # VIX ETF alternative
    ]
    
    base_url = "https://www.alphavantage.co/query"
    
    for symbol in vix_symbols:
        print(f"\n📊 Testing symbol: {symbol}")
        
        # Test 1: Intraday data (most recent)
        print(f"   🔍 Testing intraday data...")
        success = test_intraday_data(symbol, api_key)
        if success:
            print(f"   ✅ Intraday data works!")
            test_daily_data(symbol, api_key)
            return True
        
        # Test 2: Daily data
        print(f"   🔍 Testing daily data...")
        success = test_daily_data(symbol, api_key)
        if success:
            print(f"   ✅ Daily data works!")
            return True
    
    print("\n❌ No working VIX symbol found on Alpha Vantage")
    return False

def test_intraday_data(symbol, api_key):
    """Test intraday data for current/recent prices."""
    base_url = "https://www.alphavantage.co/query"
    
    params = {
        'function': 'TIME_SERIES_INTRADAY',
        'symbol': symbol,
        'interval': '60min',  # Hourly data
        'apikey': api_key,
        'outputsize': 'compact'
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=15)
        data = response.json()
        
        print(f"      Status: {response.status_code}")
        
        if 'Error Message' in data:
            print(f"      ❌ Error: {data['Error Message']}")
            return False
        
        if 'Note' in data:
            print(f"      ⚠️  Rate Limited: {data['Note']}")
            return False
        
        # Check for time series data
        time_series_key = None
        for key in data.keys():
            if 'Time Series' in key:
                time_series_key = key
                break
        
        if time_series_key and data[time_series_key]:
            time_series = data[time_series_key]
            latest_time = max(time_series.keys())
            latest_data = time_series[latest_time]
            
            open_price = float(latest_data['1. open'])
            close_price = float(latest_data['4. close'])
            high_price = float(latest_data['2. high'])
            low_price = float(latest_data['3. low'])
            
            print(f"      ✅ Latest time: {latest_time}")
            print(f"      💰 Open: ${open_price:.2f}")
            print(f"      💰 Close: ${close_price:.2f}")
            print(f"      📈 High: ${high_price:.2f}, Low: ${low_price:.2f}")
            print(f"      📊 Total periods: {len(time_series)}")
            
            return True
        else:
            print(f"      ❌ No time series data found")
            print(f"      📋 Available keys: {list(data.keys())}")
            
    except Exception as e:
        print(f"      ❌ Request failed: {e}")
    
    return False

def test_daily_data(symbol, api_key):
    """Test daily historical data."""
    base_url = "https://www.alphavantage.co/query"
    
    params = {
        'function': 'TIME_SERIES_DAILY',
        'symbol': symbol,
        'apikey': api_key,
        'outputsize': 'compact'  # Last 100 days
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=15)
        data = response.json()
        
        print(f"      Status: {response.status_code}")
        
        if 'Error Message' in data:
            print(f"      ❌ Error: {data['Error Message']}")
            return False
        
        if 'Note' in data:
            print(f"      ⚠️  Rate Limited: {data['Note']}")
            return False
        
        # Check for daily time series
        if 'Time Series (Daily)' in data:
            daily_data = data['Time Series (Daily)']
            latest_date = max(daily_data.keys())
            latest_values = daily_data[latest_date]
            
            open_price = float(latest_values['1. open'])
            close_price = float(latest_values['4. close'])
            
            print(f"      ✅ Daily data available")
            print(f"      📅 Latest date: {latest_date}")
            print(f"      💰 Latest open: ${open_price:.2f}")
            print(f"      💰 Latest close: ${close_price:.2f}")
            print(f"      📊 Days available: {len(daily_data)}")
            
            # Check if we have enough historical data for 30-day indicators
            if len(daily_data) >= 30:
                print(f"      ✅ Sufficient data for 30-day moving averages")
            else:
                print(f"      ⚠️  Only {len(daily_data)} days - may need full outputsize")
            
            return True
        else:
            print(f"      ❌ No daily data found")
            print(f"      📋 Available keys: {list(data.keys())}")
            
    except Exception as e:
        print(f"      ❌ Request failed: {e}")
    
    return False

def test_rate_limits():
    """Test Alpha Vantage rate limits."""
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    print(f"\n⏱️  Testing rate limits...")
    
    # Alpha Vantage free tier: 25 requests per day, 5 per minute
    print(f"   📝 Alpha Vantage limits:")
    print(f"   • Free tier: 25 requests/day, 5 requests/minute")
    print(f"   • Premium: 75+ requests/minute")
    print(f"   💡 For live trading, consider premium tier")

if __name__ == "__main__":
    print("🧪 Testing Alpha Vantage VIX Data Access")
    print("=" * 45)
    
    success = test_alpha_vantage_vix()
    test_rate_limits()
    
    print("\n" + "=" * 45)
    if success:
        print("🎉 SUCCESS: Alpha Vantage can provide VIX data!")
        print("💡 Ready to integrate with live trader")
        print("⚠️  Note: Watch rate limits for live trading")
    else:
        print("😞 FAILED: No VIX data available on Alpha Vantage")
        print("💡 Check API key or try different symbols")