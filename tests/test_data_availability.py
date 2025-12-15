#!/usr/bin/env python3
"""Test historical data availability from Alpaca and Yahoo Finance."""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
import yfinance as yf

load_dotenv()


def test_alpaca_tecl_history():
    """Test how far back TECL data goes on Alpaca."""
    print("=" * 60)
    print("TESTING ALPACA - TECL HISTORICAL DATA")
    print("=" * 60)

    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    if not api_key or not secret_key:
        print("❌ Alpaca credentials not found")
        return None

    try:
        data_client = StockHistoricalDataClient(api_key, secret_key)

        # TECL was launched on December 17, 2008
        # Try to get data from inception
        start_date = datetime(2008, 12, 17)
        end_date = datetime.now()

        print(f"\n📅 Requesting TECL data from {start_date.date()} to {end_date.date()}")

        request = StockBarsRequest(
            symbol_or_symbols=['TECL'],
            timeframe=TimeFrame.Day,
            start=start_date,
            end=end_date
        )

        bars = data_client.get_stock_bars(request)

        if 'TECL' in bars.data and bars.data['TECL']:
            tecl_bars = bars.data['TECL']
            first_date = tecl_bars[0].timestamp
            last_date = tecl_bars[-1].timestamp
            total_days = len(tecl_bars)

            print(f"\n✅ TECL Data Available:")
            print(f"   First available date: {first_date.date()}")
            print(f"   Last available date: {last_date.date()}")
            print(f"   Total trading days: {total_days:,}")
            print(f"   Date range: {(last_date - first_date).days:,} calendar days")

            # Show first few bars
            print(f"\n   First 3 bars:")
            for i, bar in enumerate(tecl_bars[:3]):
                print(f"   {bar.timestamp.date()}: Open=${bar.open:.2f}, Close=${bar.close:.2f}")

            # Show last few bars
            print(f"\n   Last 3 bars:")
            for bar in tecl_bars[-3:]:
                print(f"   {bar.timestamp.date()}: Open=${bar.open:.2f}, Close=${bar.close:.2f}")

            return first_date, last_date, total_days
        else:
            print("❌ No TECL data returned")
            return None

    except Exception as e:
        print(f"❌ Error fetching TECL data: {e}")
        return None


def test_yahoo_vix_history():
    """Test how far back VIX data goes on Yahoo Finance."""
    print("\n" + "=" * 60)
    print("TESTING YAHOO FINANCE - VIX HISTORICAL DATA")
    print("=" * 60)

    try:
        # VIX was introduced on January 2, 1990
        # Yahoo Finance has VIX data from early 1990s
        vix = yf.Ticker('^VIX')

        print(f"\n📅 Requesting VIX data (max available period)")

        # Get maximum available history
        hist = vix.history(period='max')

        if not hist.empty:
            first_date = hist.index[0]
            last_date = hist.index[-1]
            total_days = len(hist)

            print(f"\n✅ VIX Data Available:")
            print(f"   First available date: {first_date.date()}")
            print(f"   Last available date: {last_date.date()}")
            print(f"   Total trading days: {total_days:,}")
            print(f"   Date range: {(last_date - first_date).days:,} calendar days")

            # Show first few rows
            print(f"\n   First 3 days:")
            for i in range(min(3, len(hist))):
                row = hist.iloc[i]
                print(f"   {hist.index[i].date()}: Open={row['Open']:.2f}, Close={row['Close']:.2f}")

            # Show last few rows
            print(f"\n   Last 3 days:")
            for i in range(max(0, len(hist)-3), len(hist)):
                row = hist.iloc[i]
                print(f"   {hist.index[i].date()}: Open={row['Open']:.2f}, Close={row['Close']:.2f}")

            return first_date, last_date, total_days
        else:
            print("❌ No VIX data returned")
            return None

    except Exception as e:
        print(f"❌ Error fetching VIX data: {e}")
        return None


def test_data_overlap():
    """Test the overlap period where both datasets are available."""
    print("\n" + "=" * 60)
    print("ANALYZING DATA OVERLAP FOR BACKTESTING")
    print("=" * 60)

    # TECL inception: December 17, 2008
    tecl_start = datetime(2008, 12, 17)

    print(f"\n📊 Backtest Data Availability:")
    print(f"   TECL launched: {tecl_start.date()}")
    print(f"   VIX data: Available since ~1990")
    print(f"\n   ✅ Maximum backtest period: {tecl_start.date()} to present")
    print(f"   📅 That's approximately {(datetime.now() - tecl_start).days / 365.25:.1f} years")

    # Calculate expected trading days (rough estimate: ~252 per year)
    years = (datetime.now() - tecl_start).days / 365.25
    estimated_days = int(years * 252)

    print(f"   📈 Estimated trading days: ~{estimated_days:,}")

    print(f"\n💡 Note: TECL is a leveraged ETF created in 2008")
    print(f"   - You CANNOT backtest before December 17, 2008")
    print(f"   - For longer backtests, you would need to use:")
    print(f"     • QQQ (non-leveraged tech ETF, since 1999)")
    print(f"     • SPY (S&P 500 ETF, since 1993)")
    print(f"     • Or simulate 3x leverage manually on tech indices")


def main():
    """Run all data availability tests."""
    print("\n🔍 HISTORICAL DATA AVAILABILITY TEST")
    print("Testing how far back we can backtest your algorithm\n")

    # Test TECL
    tecl_result = test_alpaca_tecl_history()

    # Test VIX
    vix_result = test_yahoo_vix_history()

    # Analyze overlap
    test_data_overlap()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    if tecl_result and vix_result:
        tecl_first, tecl_last, tecl_days = tecl_result
        vix_first, vix_last, vix_days = vix_result

        # The limiting factor is TECL (newer)
        backtest_start = max(tecl_first, datetime(2008, 12, 17))
        backtest_end = min(tecl_last, vix_last)

        print(f"\n✅ You can backtest from:")
        print(f"   Start: {backtest_start.date()}")
        print(f"   End: {backtest_end.date()}")
        print(f"   Duration: {(backtest_end - backtest_start).days / 365.25:.1f} years")

        print(f"\n📋 To backtest the full period:")
        print(f"   1. Download TECL data from Alpaca (Dec 2008 - present)")
        print(f"   2. Download VIX data from Yahoo Finance (same period)")
        print(f"   3. Run your backtesting script")

        print(f"\n⚠️  Important considerations:")
        print(f"   • TECL is 3x leveraged - extreme volatility")
        print(f"   • This period includes 2008 crisis recovery")
        print(f"   • 2020 COVID crash and recovery")
        print(f"   • 2022 tech sell-off")
        print(f"   • Recent 2023-2024 AI boom")
    else:
        print("\n❌ Could not determine full backtest period")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
