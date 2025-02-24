import pandas as pd
import numpy as np
import sys

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
    
    if date_col != 'Date':
        df = df.rename(columns={date_col: 'Date'})
    return df

def add_suffix(df, suffix):
    """
    Add a suffix to all columns except 'Date'.
    """
    return df.rename(columns={col: f"{col}{suffix}" if col != "Date" else col for col in df.columns})

def merge_data(tecl_df, vix_df):
    """
    Merge the two DataFrames on the 'Date' column using an inner join.
    Only dates that are present in both datasets will be included.
    """
    merged_df = pd.merge(tecl_df, vix_df, on='Date', how='inner')
    merged_df.sort_values('Date', inplace=True)
    merged_df.set_index('Date', inplace=True)
    return merged_df

def calculate_indicators(merged_df):
    """
    Calculate the indicators:
      - 45-day simple moving average (SMA) for TECL using the 'Open_tecl' column.
      - 30-day weighted moving average (WMA) for VIX using the 'OPEN_vix' column.
    """
    merged_df['SMA_tecl'] = merged_df['Open_tecl'].rolling(window=45, min_periods=45).mean()
    weights = np.arange(1, 31)
    merged_df['WMA_vix'] = merged_df['OPEN_vix'].rolling(window=30, min_periods=30).apply(
        lambda x: np.dot(x, weights) / weights.sum(), raw=True
    )
    return merged_df

# def backtest_trading(merged_df, initial_fund=10000):
#     """
#     Simulate the trading strategy day by day.
    
#     Trading logic:
#       - Start with initial_fund dollars.
#       - If not in a position:
#           * If TECL < 0.75 * SMA_tecl, buy immediately.
#           * Else, if VIX > 1.04 * WMA_vix, trigger a waiting period of 5 days.
#             Once the waiting period is over, if TECL < 1.25 * SMA_tecl, then buy.
#       - If in a position:
#           * Sell when TECL price >= 1.05 * purchase price.
    
#     Returns a list of trade records and the final fund value.
#     """
#     fund = initial_fund
#     in_position = False
#     purchase_price = None
#     waiting_until = None
#     trades = []
    
#     # Iterate day by day (index is Date)
#     for current_date, row in merged_df.iterrows():
#         tecl_price = row['Open_tecl']
#         vix_price = row['OPEN_vix']
#         sma = row['SMA_tecl']
#         wma = row['WMA_vix']
        
#         if pd.isna(sma) and pd.isna(wma):
#             continue
        
#         # If in a position, check sell criteria:
#         if in_position:
#             if tecl_price >= purchase_price * 1.0575:
#                 # Sell entire position
#                 sell_price = tecl_price
#                 fund = fund * (sell_price / purchase_price)
#                 trades.append({
#                     'date': current_date,
#                     'action': 'sell',
#                     'price': sell_price,
#                     'fund': fund
#                 })
#                 in_position = False
#                 purchase_price = None
#                 waiting_until = None
#             # continue
        
#         # Not in position:
#         if waiting_until is not None and not in_position:
#             if current_date >= waiting_until:
#                 # Waiting period ended; check if TECL < 1.25 * SMA_tecl
#                 if tecl_price < 1.25 * sma:
#                     purchase_price = tecl_price
#                     in_position = True
#                     trades.append({
#                         'date': current_date,
#                         'action': 'buy (after wait)',
#                         'price': tecl_price,
#                         'fund': fund
#                     })
#                 waiting_until = None
#             continue
        
#         # Check immediate entry condition (Second criteria): TECL < 0.75 * SMA_tecl
#         if tecl_price < 0.75 * sma and not in_position:
#             purchase_price = tecl_price
#             in_position = True
#             trades.append({
#                 'date': current_date,
#                 'action': 'buy (immediate low TECL)',
#                 'price': tecl_price,
#                 'fund': fund
#             })
#             continue
        
#         # Check first criteria: if VIX > 1.04 * WMA_vix, trigger waiting period.
#         if vix_price > 1.04 * wma:
#             # Change this to be 5 trading days instead of 7 days
#             waiting_until = current_date + pd.offsets.BDay(4)
#             trades.append({
#                 'date': current_date,
#                 'action': 'waiting signal triggered',
#                 'vix': vix_price,
#                 'WMA_vix': wma,
#                 'wait_until': waiting_until
#             })
            
#     return trades, fund

# def backtest_trading(merged_df, initial_fund=10000):
#     """
#     Simulate the trading strategy day by day.

#     Trading logic:
#       - Start with initial_fund dollars.
#       - If not in a position:
#           * If TECL < 0.75 * SMA_tecl, buy immediately.
#           * Else, if TECL < 1.25 * SMA_tecl, then look back 4 business days.
#                 If on that day VIX > 1.04 * WMA_vix, buy.
#       - If in a position:
#           * Sell when TECL price >= 1.0575 * purchase price.

#     Returns a list of trade records and the final fund value.
#     """
#     fund = initial_fund
#     in_position = False
#     purchase_price = None
#     trades = []
    
#     # Iterate day by day (index is Date)
#     for current_date, row in merged_df.iterrows():
#         tecl_price = row['Open_tecl']
#         # Although we don't use today's VIX for the VIX condition, we still need it for indicator validation.
#         vix_price = row['OPEN_vix']
#         sma = row['SMA_tecl']
#         wma = row['WMA_vix']
        
#         # Skip days until both indicators are valid
#         if pd.isna(sma) or pd.isna(wma):
#             continue
        
#         # If in a position, check sell criteria:
#         if in_position:
#             if tecl_price >= purchase_price * 1.0575:
#                 sell_price = tecl_price
#                 fund = fund * (sell_price / purchase_price)
#                 trades.append({
#                     'date': current_date,
#                     'action': 'sell',
#                     'price': sell_price,
#                     'fund': fund
#                 })
#                 in_position = False
#                 purchase_price = None
#             # When in a position, do not consider any new buy signals.
#             continue
        
#         # Not in position:
#         # 1. Immediate buy if TECL < 0.75 * SMA_tecl
#         if tecl_price < 0.75 * sma:
#             purchase_price = tecl_price
#             in_position = True
#             trades.append({
#                 'date': current_date,
#                 'action': 'buy (immediate low TECL)',
#                 'price': tecl_price,
#                 'fund': fund
#             })
#             continue
        
#         # 2. Check if TECL < 1.25 * SMA_tecl. If yes, check VIX condition from 4 business days ago.
#         if tecl_price < 1.25 * sma:
#             prev_date = current_date - pd.offsets.BDay(4)
#             if prev_date in merged_df.index:
#                 prev_row = merged_df.loc[prev_date]
#                 if prev_row['OPEN_vix'] > 1.04 * prev_row['WMA_vix']:
#                     purchase_price = tecl_price
#                     in_position = True
#                     trades.append({
#                         'date': current_date,
#                         'action': 'buy (with VIX condition)',
#                         'price': tecl_price,
#                         'fund': fund,
#                         'prev_date': prev_date,
#                         'prev_vix': prev_row['OPEN_vix'],
#                         'prev_WMA_vix': prev_row['WMA_vix']
#                     })
#                     continue

#     return trades, fund
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

    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')

    years = (end_date - start_date).days / 365.25

    return_value = (final_fund / starting_fund) ** (1 / years) - 1

    return return_value * 100

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
    fund = initial_fund
    in_position = False
    purchase_price = None
    trades = []
    last_sell_date = None  # Track the date of the most recent sell

    # Iterate day by day (index is Date)
    for current_date, row in merged_df.iterrows():
        tecl_price = row['Open_tecl']
        vix_price = row['OPEN_vix']
        sma = row['SMA_tecl']
        wma = row['WMA_vix']

        # Skip days until both indicators are valid
        if pd.isna(sma) or pd.isna(wma):
            continue

        # If in a position, check sell criteria:
        if in_position:
            if tecl_price >= purchase_price * 1.0575:
                sell_price = tecl_price
                fund = fund * (sell_price / purchase_price)
                trades.append({
                    'date': current_date,
                    'action': 'sell',
                    'price': sell_price,
                    'fund': fund
                })
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
            trades.append({
                'date': current_date,
                'action': 'buy (immediate low TECL)',
                'price': tecl_price,
                'fund': fund
            })
            continue

        # 2. If TECL < 1.25 * SMA_tecl, check the VIX condition from 4 rows earlier.
        if tecl_price < 1.25 * sma:
            # Get the positional index of the current date
            pos = merged_df.index.get_loc(current_date)
            if pos >= 4:
                prev_date = merged_df.index[pos - 4]
                prev_row = merged_df.loc[prev_date]
                if prev_row['OPEN_vix'] > 1.04 * prev_row['WMA_vix']:
                    purchase_price = tecl_price
                    in_position = True
                    trades.append({
                        'date': current_date,
                        'action': 'buy (with VIX condition)',
                        'price': tecl_price,
                        'fund': fund,
                        'prev_date': prev_date,
                        'prev_vix': prev_row['OPEN_vix'],
                        'prev_WMA_vix': prev_row['WMA_vix']
                    })
                    continue

    return trades, fund


  


if __name__ == '__main__':
    tecl_file = 'tecl_history5.csv'
    vix_file = 'vix_history.csv'
    
    tecl_df = load_data(tecl_file, 'Date')
    vix_df = load_data(vix_file, 'DATE')
    
    tecl_df = add_suffix(tecl_df, '_tecl')
    vix_df = add_suffix(vix_df, '_vix')
    
    merged_df = merge_data(tecl_df, vix_df)
    
    merged_df = calculate_indicators(merged_df)
    
    trades, final_fund = backtest_trading(merged_df)
    
    for trade in trades:
        print(trade)
    print(f"Final fund value: ${final_fund:.2f}")
    
    starting_fund = 10000
    start_date = '2008-12-17'
    end_date = '2025-02-21'
    
    annualized_return_value = annualized_return(starting_fund, final_fund, start_date, end_date)
    print(f"The annualized return is: {annualized_return_value:.2f}%")
    # print(merged_df.to_string())
