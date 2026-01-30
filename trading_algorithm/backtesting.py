import pandas as pd
import numpy as np
import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'backtesting.log')),
        logging.StreamHandler()
    ]
)


def load_data(file_path, date_col):
    """
    Load CSV data into a DataFrame.
    Strips whitespace from headers and date strings, converts the date column,
    and renames it to 'Date'.
    """
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()
    if date_col not in df.columns:
        raise ValueError(f"Expected column '{date_col}' not found in file {file_path}")
    df[date_col] = df[date_col].astype(str).str.strip()
    df[date_col] = pd.to_datetime(df[date_col])

    if date_col != "Date":
        df = df.rename(columns={date_col: "Date"})
    return df


def add_suffix(df, suffix):
    """
    Add a suffix to all columns except 'Date'.
    """
    return df.rename(
        columns={col: f"{col}{suffix}" if col != "Date" else col for col in df.columns}
    )


def merge_data(tecl_df, vix_df):
    """
    Merge the two DataFrames on the 'Date' column using an inner join.
    Only dates that are present in both datasets will be included.
    """
    merged_df = pd.merge(tecl_df, vix_df, on="Date", how="inner")
    merged_df.sort_values("Date", inplace=True)
    merged_df.set_index("Date", inplace=True)
    return merged_df


def calculate_indicators(merged_df):
    """
    Calculate the indicators:
      - 30-day simple moving average (SMA) for TECL using the 'Open_tecl' column.
      - 30-day weighted moving average (WMA) for VIX using the 'OPEN_vix' column.

    IMPORTANT: Indicators are shifted by 1 day to avoid look-ahead bias.
    This means on day T, we use the SMA/WMA calculated from days T-30 to T-1.
    """
    # Calculate rolling averages
    merged_df["SMA_tecl"] = merged_df["Open_tecl"].rolling(window=30, min_periods=30).mean()
    weights = np.arange(1, 31)
    merged_df["WMA_vix"] = (
        merged_df["OPEN_vix"]
        .rolling(window=30, min_periods=30)
        .apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
    )

    # Shift indicators by 1 day to use only historical data
    # On day T, SMA_tecl and WMA_vix reflect data from T-30 to T-1 (not including T)
    merged_df["SMA_tecl"] = merged_df["SMA_tecl"].shift(1)
    merged_df["WMA_vix"] = merged_df["WMA_vix"].shift(1)

    return merged_df


def annualized_return(starting_fund, final_fund, start_date, end_date):
    """
    Calculate the annualized return of an investment.

    Parameters:
    starting_fund (float): The initial amount of money invested.
    final_fund (float): The amount of money at the end of the investment period.
    start_date (str): The start date of the investment period in 'YYYY-MM-DD' format.
    end_date (str): The end date of the investment period in 'YYYY-MM-DD' format.

    Returns:
    float: The annualized return as a percentage.
    """
    from datetime import datetime

    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")

    years = (end_date - start_date).days / 365.25

    return_value = (final_fund / starting_fund) ** (1 / years) - 1

    return return_value * 100


def fetch_live_data(use_vxx=False):
    """
    Fetch historical data from Alpaca (TECL) and either Yahoo Finance (VIX) or Alpaca (VXX).

    Args:
        use_vxx: If True, fetch VXX from Alpaca instead of VIX from Yahoo Finance

    Returns DataFrames ready for backtesting.
    """
    import yfinance as yf
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame

    volatility_symbol = "VXX" if use_vxx else "VIX"
    print(f"📡 Fetching live data from APIs (using {volatility_symbol})...")

    # Get Alpaca credentials
    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')

    if not api_key or not secret_key:
        raise ValueError("Alpaca API credentials not found. Check your .env file.")

    # Initialize Alpaca client
    data_client = StockHistoricalDataClient(api_key, secret_key)

    # Get maximum available data (Alpaca free tier: ~2016 to present)
    end_date = datetime.now()
    start_date = datetime(2016, 1, 1)  # Alpaca's data starts around here

    # Fetch TECL data from Alpaca
    print("   Fetching TECL data from Alpaca...")
    request = StockBarsRequest(
        symbol_or_symbols=['TECL'],
        timeframe=TimeFrame.Day,
        start=start_date,
        end=end_date
    )

    bars = data_client.get_stock_bars(request)

    if 'TECL' not in bars.data or not bars.data['TECL']:
        raise ValueError("No TECL data returned from Alpaca")

    # Convert to DataFrame
    tecl_data = []
    for bar in bars.data['TECL']:
        tecl_data.append({
            'Date': bar.timestamp.date(),
            'Open': float(bar.open),
            'High': float(bar.high),
            'Low': float(bar.low),
            'Close': float(bar.close),
            'Volume': int(bar.volume)
        })

    tecl_df = pd.DataFrame(tecl_data)
    tecl_df['Date'] = pd.to_datetime(tecl_df['Date'])
    print(f"   ✅ TECL: {len(tecl_df)} days ({tecl_df['Date'].min().date()} to {tecl_df['Date'].max().date()})")

    # Fetch volatility data (VXX from Alpaca or VIX from Yahoo Finance)
    if use_vxx:
        print("   Fetching VXX data from Alpaca...")
        request_vxx = StockBarsRequest(
            symbol_or_symbols=['VXX'],
            timeframe=TimeFrame.Day,
            start=start_date,
            end=end_date
        )

        bars_vxx = data_client.get_stock_bars(request_vxx)

        if 'VXX' not in bars_vxx.data or not bars_vxx.data['VXX']:
            raise ValueError("No VXX data returned from Alpaca")

        # Convert to DataFrame with consistent format
        vxx_data = []
        for bar in bars_vxx.data['VXX']:
            vxx_data.append({
                'Date': bar.timestamp.date(),
                'OPEN': float(bar.open),
                'HIGH': float(bar.high),
                'LOW': float(bar.low),
                'CLOSE': float(bar.close),
                'Volume': int(bar.volume)
            })

        vix_df = pd.DataFrame(vxx_data)
        vix_df['Date'] = pd.to_datetime(vix_df['Date'])
        print(f"   ✅ VXX: {len(vix_df)} days ({vix_df['Date'].min().date()} to {vix_df['Date'].max().date()})")
    else:
        print("   Fetching VIX data from Yahoo Finance...")
        vix = yf.Ticker('^VIX')
        vix_hist = vix.history(start=start_date, end=end_date)

        if vix_hist.empty:
            raise ValueError("No VIX data returned from Yahoo Finance")

        # Convert to DataFrame with consistent format
        vix_df = pd.DataFrame({
            'Date': vix_hist.index.date,
            'OPEN': vix_hist['Open'].values,
            'HIGH': vix_hist['High'].values,
            'LOW': vix_hist['Low'].values,
            'CLOSE': vix_hist['Close'].values
        })
        vix_df['Date'] = pd.to_datetime(vix_df['Date'])
        print(f"   ✅ VIX: {len(vix_df)} days ({vix_df['Date'].min().date()} to {vix_df['Date'].max().date()})")

    print("✅ Data fetched successfully!\n")

    return tecl_df, vix_df


def backtest_trading(merged_df, initial_fund=10000):
    """
    Simulate the trading strategy day by day.

    Trading logic:
      - Start with initial_fund dollars.
      - If not in a position:
          * If TECL < 0.75 * SMA_tecl, buy immediately.
          * Else, if TECL < 1.25 * SMA_tecl, then look back 4 rows (i.e. 4 days in the dataframe).
                If on that day VIX > 1.04 * WMA_vix, buy.
      - If in a position:
          * Sell when TECL price >= 1.0575 * purchase price.
      - Ignore any buy signals on the day immediately following a sell signal.

    Returns a list of trade records and the final fund value.
    """
    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info("STARTING BACKTEST")
    logger.info(f"Initial fund: ${initial_fund:,.2f}")
    logger.info("=" * 80)

    fund = initial_fund
    bank = 0  # Initialize bank to hold 20% of profits
    in_position = False
    purchase_price = None
    trades = []
    last_sell_date = None  # Track the date of the most recent sell

    # Iterate day by day (index is Date)
    for current_date, row in merged_df.iterrows():
        tecl_price = row["Open_tecl"]
        vix_price = row["OPEN_vix"]
        sma = row["SMA_tecl"]
        wma = row["WMA_vix"]

        # Skip days until both indicators are valid
        if pd.isna(sma) or pd.isna(wma):
            continue

        # If in a position, check sell criteria:
        if in_position:
            if tecl_price >= purchase_price * 1.058:
                sell_price = tecl_price
                profit = fund * (sell_price / purchase_price) - fund
                bank += profit * 0.2  # Take out 20% of profits to the bank
                fund = fund * (sell_price / purchase_price)  # Update fund with remaining profit

                trade_record = {
                    "date": current_date,
                    "action": "sell",
                    "price": sell_price,
                    "fund": fund,
                    "bank": bank,
                }
                trades.append(trade_record)

                # Format datetime appropriately based on index type
                date_str = current_date.strftime('%Y-%m-%d %H:%M') if hasattr(current_date, 'hour') else str(current_date.date())
                logger.info(f"SELL  | {date_str} | Price: ${sell_price:.2f} | "
                           f"Profit: ${profit:.2f} | Fund: ${fund:,.2f} | Bank: ${bank:,.2f}")

                in_position = False
                purchase_price = None
                last_sell_date = current_date  # Record the sell date
            # Once sold (or if still in position), don't process any buy signals.
            continue

        # If not in a position, ignore buy signals on the day immediately following a sell.
        if last_sell_date is not None and current_date == (last_sell_date + pd.offsets.BDay(1)):
            continue

        # 1. Immediate buy if TECL < 0.75 * SMA_tecl
        if tecl_price < 0.75 * sma:
            purchase_price = tecl_price
            in_position = True

            trade_record = {
                "date": current_date,
                "action": "buy (immediate low TECL)",
                "price": tecl_price,
                "fund": fund,
            }
            trades.append(trade_record)

            date_str = current_date.strftime('%Y-%m-%d %H:%M') if hasattr(current_date, 'hour') else str(current_date.date())
            logger.info(f"BUY   | {date_str} | Price: ${tecl_price:.2f} | "
                       f"Reason: Immediate low TECL (${tecl_price:.2f} < 0.75*${sma:.2f}) | Fund: ${fund:,.2f}")
            continue

        # 2. If TECL < 1.25 * SMA_tecl, check the VIX condition from 4 rows earlier.
        if tecl_price < 1.25 * sma:
            # Get the positional index of the current date
            pos = merged_df.index.get_loc(current_date)
            if pos >= 4:
                prev_date = merged_df.index[pos - 4]
                prev_row = merged_df.loc[prev_date]
                if prev_row["OPEN_vix"] > 1.04 * prev_row["WMA_vix"]:
                    purchase_price = tecl_price
                    in_position = True

                    trade_record = {
                        "date": current_date,
                        "action": "buy (with VIX condition)",
                        "price": tecl_price,
                        "fund": fund,
                        "prev_date": prev_date,
                        "prev_vix": prev_row["OPEN_vix"],
                        "prev_WMA_vix": prev_row["WMA_vix"],
                    }
                    trades.append(trade_record)

                    date_str = current_date.strftime('%Y-%m-%d %H:%M') if hasattr(current_date, 'hour') else str(current_date.date())
                    logger.info(f"BUY   | {date_str} | Price: ${tecl_price:.2f} | "
                               f"Reason: VIX condition (4 rows ago VIX ${prev_row['OPEN_vix']:.2f} > 1.04*${prev_row['WMA_vix']:.2f}) | Fund: ${fund:,.2f}")
                    continue

    logger.info("=" * 80)
    logger.info(f"BACKTEST COMPLETE - Total trades: {len(trades)}")
    logger.info("=" * 80)

    return trades, fund, bank  # Return bank along with trades and fund


def main(use_live_data=False, use_vxx=False):
    """Main entry point for backtesting.

    Args:
        use_live_data: If True, fetch data from APIs instead of CSV files
        use_vxx: If True, use VXX instead of VIX (only applies when use_live_data=True)
    """
    starting_fund = 10000

    if use_live_data:
        volatility_source = "VXX (Alpaca)" if use_vxx else "VIX (Yahoo Finance)"
        print(f"🔴 LIVE DATA MODE - Fetching from APIs")
        print(f"   Volatility Source: {volatility_source}")
        print("=" * 50)
        # Fetch data from APIs
        tecl_df, vix_df = fetch_live_data(use_vxx=use_vxx)

        # Add suffixes
        tecl_df = add_suffix(tecl_df, "_tecl")
        vix_df = add_suffix(vix_df, "_vix")
    else:
        print("📁 CSV DATA MODE - Using local files")
        print("=" * 50)
        # Load from CSV files
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        tecl_file = os.path.join(data_dir, "tecl_history5.csv")
        vix_file = os.path.join(data_dir, "vix_history.csv")

        tecl_df = load_data(tecl_file, "Date")
        vix_df = load_data(vix_file, "DATE")

        tecl_df = add_suffix(tecl_df, "_tecl")
        vix_df = add_suffix(vix_df, "_vix")

    # Merge data
    merged_df = merge_data(tecl_df, vix_df)

    # Calculate indicators
    merged_df = calculate_indicators(merged_df)

    # Run backtest
    print("🤖 Running backtest...")
    trades, final_fund, final_bank = backtest_trading(merged_df, initial_fund=starting_fund)

    # Get date range from data
    start_date = merged_df.index.min().strftime('%Y-%m-%d')
    end_date = merged_df.index.max().strftime('%Y-%m-%d')

    # Calculate annualized return
    annual_return = annualized_return(starting_fund, final_fund, start_date, end_date)

    # Calculate buy-and-hold comparison
    first_tecl_price = merged_df['Open_tecl'].iloc[0]
    last_tecl_price = merged_df['Open_tecl'].iloc[-1]
    shares_if_held = starting_fund / first_tecl_price
    buy_and_hold_value = shares_if_held * last_tecl_price
    buy_and_hold_return = ((buy_and_hold_value / starting_fund) - 1) * 100
    buy_and_hold_annual = annualized_return(starting_fund, buy_and_hold_value, start_date, end_date)

    # Print results
    print("\n" + "=" * 50)
    print("TRADING ALGORITHM BACKTEST RESULTS")
    print("=" * 50)
    print(f"Period: {start_date} to {end_date}")
    print(f"Total trades: {len(trades)}")
    print(f"Initial investment: ${starting_fund:,.2f}")
    print(f"Final fund value: ${final_fund:,.2f}")
    print(f"Total in bank: ${final_bank:,.2f}")
    print(f"Combined total: ${final_fund + final_bank:,.2f}")
    print(f"Total return: {((final_fund + final_bank) / starting_fund - 1) * 100:.2f}%")
    print(f"Annualized return: {annual_return:.2f}%")
    print()
    print("BUY AND HOLD COMPARISON")
    print("=" * 50)
    print(f"TECL price on {start_date}: ${first_tecl_price:.2f}")
    print(f"TECL price on {end_date}: ${last_tecl_price:.2f}")
    print(f"Shares purchased: {shares_if_held:.2f}")
    print(f"Buy-and-hold value: ${buy_and_hold_value:,.2f}")
    print(f"Buy-and-hold return: {buy_and_hold_return:.2f}%")
    print(f"Buy-and-hold annualized: {buy_and_hold_annual:.2f}%")
    print()
    print("PERFORMANCE COMPARISON")
    print("=" * 50)
    algorithm_total = final_fund + final_bank
    outperformance = algorithm_total - buy_and_hold_value
    outperformance_pct = ((algorithm_total / buy_and_hold_value) - 1) * 100
    print(f"Algorithm total: ${algorithm_total:,.2f}")
    print(f"Buy-and-hold total: ${buy_and_hold_value:,.2f}")
    print(f"Difference: ${outperformance:,.2f} ({outperformance_pct:+.2f}%)")
    if outperformance > 0:
        print(f"✅ Algorithm OUTPERFORMED buy-and-hold by {outperformance_pct:.2f}%")
    else:
        print(f"❌ Algorithm UNDERPERFORMED buy-and-hold by {abs(outperformance_pct):.2f}%")
    print("=" * 50)

    return trades, final_fund, final_bank


def cli_main():
    """CLI entry point that doesn't return anything."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Backtest the TECL trading algorithm',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use CSV files (default)
  python -m trading_algorithm.backtesting

  # Fetch fresh data from APIs using VIX from Yahoo Finance
  python -m trading_algorithm.backtesting --live-data

  # Fetch fresh data from APIs using VXX from Alpaca
  python -m trading_algorithm.backtesting --live-data --use-vxx
        """
    )
    parser.add_argument(
        '--live-data',
        action='store_true',
        help='Fetch fresh data from Alpaca and Yahoo Finance APIs instead of using CSV files'
    )
    parser.add_argument(
        '--use-vxx',
        action='store_true',
        help='Use VXX from Alpaca instead of VIX from Yahoo Finance (requires --live-data)'
    )

    args = parser.parse_args()

    if args.use_vxx and not args.live_data:
        parser.error("--use-vxx requires --live-data")

    main(use_live_data=args.live_data, use_vxx=args.use_vxx)


if __name__ == "__main__":
    cli_main()
