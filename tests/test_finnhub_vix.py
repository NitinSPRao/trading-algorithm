#!/usr/bin/env python3
"""Quick test script to check Finnhub VIX data availability."""

import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_finnhub_vix():
    """Test Finnhub API for VIX data access."""
    api_key = os.getenv('FINNHUB_API_KEY')
    
    if not api_key:
        print("❌ FINNHUB_API_KEY not found in .env file")
        return False
    
    print(f"🔑 Using Finnhub API Key: {api_key[:8]}...")
    
    # Test different VIX symbol variations
    vix_symbols = [
        'VIX',
        '^VIX', 
        'VIX.I',
        'VXX',  # VIX ETF alternative
        '.VIX'
    ]
    
    base_url = "https://finnhub.io/api/v1"
    
    for symbol in vix_symbols:
        print(f"\n📊 Testing symbol: {symbol}")
        
        # Test 1: Current quote
        quote_url = f"{base_url}/quote"
        params = {
            'symbol': symbol,
            'token': api_key
        }
        
        try:
            response = requests.get(quote_url, params=params, timeout=10)
            data = response.json()
            
            print(f"   Quote Response: {response.status_code}")
            
            if response.status_code == 200:
                if 'c' in data and data['c'] is not None and data['c'] > 0:
                    print(f"   ✅ Current Price: ${data['c']}")
                    print(f"   📈 High: ${data.get('h', 'N/A')}, Low: ${data.get('l', 'N/A')}")
                    print(f"   📊 Open: ${data.get('o', 'N/A')}, Previous Close: ${data.get('pc', 'N/A')}")
                    
                    # Test 2: Historical data
                    print(f"   🔍 Testing historical data...")
                    test_historical_data(symbol, api_key)
                    return True
                else:
                    print(f"   ❌ No valid price data: {data}")
            else:
                print(f"   ❌ API Error: {data}")
                
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
    
    print("\n❌ No working VIX symbol found on Finnhub")
    return False

def test_historical_data(symbol, api_key):
    """Test historical data for a symbol."""
    base_url = "https://finnhub.io/api/v1"
    
    # Get data for last 10 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=10)
    
    # Convert to Unix timestamps
    start_ts = int(start_date.timestamp())
    end_ts = int(end_date.timestamp())
    
    candle_url = f"{base_url}/stock/candle"
    params = {
        'symbol': symbol,
        'resolution': 'D',  # Daily
        'from': start_ts,
        'to': end_ts,
        'token': api_key
    }
    
    try:
        response = requests.get(candle_url, params=params, timeout=10)
        data = response.json()
        
        if response.status_code == 200 and data.get('s') == 'ok':
            opens = data.get('o', [])
            closes = data.get('c', [])
            times = data.get('t', [])
            
            print(f"   ✅ Historical data: {len(opens)} days")
            
            if opens and len(opens) > 0:
                print(f"   📅 Latest date: {datetime.fromtimestamp(times[-1]).strftime('%Y-%m-%d')}")
                print(f"   💰 Latest open: ${opens[-1]:.2f}")
                print(f"   💰 Latest close: ${closes[-1]:.2f}")
                return True
        else:
            print(f"   ❌ Historical data failed: {data}")
            
    except Exception as e:
        print(f"   ❌ Historical request failed: {e}")
    
    return False

if __name__ == "__main__":
    print("🧪 Testing Finnhub VIX Data Access")
    print("=" * 40)
    
    success = test_finnhub_vix()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 SUCCESS: Finnhub can provide VIX data!")
        print("💡 Ready to integrate with live trader")
    else:
        print("😞 FAILED: No VIX data available on Finnhub")
        print("💡 Consider alternative data sources (Yahoo Finance, Alpha Vantage)")