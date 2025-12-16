"""Live trading implementation using Alpaca API."""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import pandas as pd
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from dotenv import load_dotenv
import yfinance as yf

from .backtesting import calculate_indicators

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))
logger = logging.getLogger(__name__)


class AlpacaLiveTrader:
    """Live trading implementation using Alpaca API."""
    
    def __init__(self):
        """Initialize the live trader with Alpaca credentials."""
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.secret_key = os.getenv('ALPACA_SECRET_KEY') 
        self.base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets/v2')
        
        if not self.api_key or not self.secret_key:
            raise ValueError("Alpaca API credentials not found. Check your .env file.")
            
        # Initialize trading client (using Yahoo Finance for market data)
        self.trading_client = TradingClient(self.api_key, self.secret_key, paper=True)
        
        # Trading state
        self.in_position = False
        self.purchase_price = None
        self.position_size = 0
        self.last_sell_date = None
        
        # Configuration
        self.position_size_limit = float(os.getenv('POSITION_SIZE_LIMIT', 0.95))
        
        logger.info("AlpacaLiveTrader initialized successfully")
    
    def get_account_info(self) -> dict[str, Any]:
        """Get current account information."""
        account = self.trading_client.get_account()
        return {
            'buying_power': float(account.buying_power),
            'portfolio_value': float(account.portfolio_value),
            'cash': float(account.cash),
            'day_trade_buying_power': float(getattr(account, 'day_trade_buying_power', account.buying_power))
        }
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol."""
        try:
            # Use Yahoo Finance for all symbols to avoid Alpaca SIP subscription issues
            if symbol == 'VIX':
                ticker = yf.Ticker('^VIX')
            else:
                ticker = yf.Ticker(symbol)

            hist = ticker.history(period='1d')
            if not hist.empty:
                return float(hist['Close'].iloc[-1])
            return None
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, days: int = 60) -> pd.DataFrame:
        """Get historical data for indicator calculations."""
        try:
            # Use Yahoo Finance for all symbols to avoid Alpaca SIP subscription issues
            if symbol == 'VIX':
                ticker = yf.Ticker('^VIX')
            else:
                ticker = yf.Ticker(symbol)

            hist = ticker.history(period=f'{days}d')

            if not hist.empty:
                # Rename columns to match expected format
                hist = hist.rename(columns={
                    'Open': 'Open',
                    'High': 'High',
                    'Low': 'Low',
                    'Close': 'Close',
                    'Volume': 'Volume'
                })
                return hist
            else:
                logger.warning(f"No data found for {symbol} from Yahoo Finance")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    def place_order(self, symbol: str, side: OrderSide, qty: float) -> bool:
        """Place a market order."""
        try:
            order_request = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=side,
                time_in_force=TimeInForce.DAY
            )
            
            order = self.trading_client.submit_order(order_request)
            logger.info(f"Order submitted: {side} {qty} shares of {symbol}, Order ID: {order.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error placing {side} order for {symbol}: {e}")
            return False
    
    def buy_tecl(self, price: float, reason: str) -> bool:
        """Execute a buy order for TECL."""
        if self.in_position:
            logger.warning("Already in position, skipping buy signal")
            return False
            
        account_info = self.get_account_info()
        buying_power = account_info['buying_power']
        
        # Calculate position size (use configured limit of buying power)
        position_value = buying_power * self.position_size_limit
        shares = int(position_value // price)
        
        if shares < 1:
            logger.warning(f"Insufficient buying power for TECL at ${price}")
            return False
        
        if self.place_order('TECL', OrderSide.BUY, shares):
            self.in_position = True
            self.purchase_price = price
            self.position_size = shares
            logger.info(f"BUY: {shares} shares of TECL at ${price:.2f} - {reason}")
            return True
        return False
    
    def sell_tecl(self, price: float) -> bool:
        """Execute a sell order for TECL."""
        if not self.in_position:
            logger.warning("Not in position, skipping sell signal")
            return False
        
        if self.place_order('TECL', OrderSide.SELL, self.position_size):
            profit_pct = (price / self.purchase_price - 1) * 100
            logger.info(f"SELL: {self.position_size} shares of TECL at ${price:.2f} - Profit: {profit_pct:.2f}%")
            
            self.in_position = False
            self.purchase_price = None
            self.position_size = 0
            self.last_sell_date = datetime.now().date()
            return True
        return False
    
    def check_trading_signals(self) -> None:
        """Check for trading signals and execute trades."""
        # Get current prices
        tecl_price = self.get_current_price('TECL')
        vix_price = self.get_current_price('VIX')
        
        if not tecl_price or not vix_price:
            logger.warning("Could not get current prices")
            return
        
        # Get historical data for indicators
        tecl_data = self.get_historical_data('TECL')
        vix_data = self.get_historical_data('VIX')
        
        if tecl_data.empty or vix_data.empty:
            logger.warning("Could not get historical data")
            return
        
        # Prepare data similar to backtesting
        tecl_data = tecl_data.rename(columns={'Open': 'Open_tecl'})
        vix_data = vix_data.rename(columns={'Open': 'OPEN_vix'})
        
        # Remove timezone info to avoid merge issues
        if tecl_data.index.tz is not None:
            tecl_data.index = tecl_data.index.tz_localize(None)
        if vix_data.index.tz is not None:
            vix_data.index = vix_data.index.tz_localize(None)
        
        # Merge data
        merged_df = pd.merge(tecl_data[['Open_tecl']], vix_data[['OPEN_vix']], 
                           left_index=True, right_index=True, how='inner')
        
        if len(merged_df) < 30:
            logger.warning("Insufficient historical data for indicators")
            return
        
        # Calculate indicators
        merged_df = calculate_indicators(merged_df)
        
        # Get latest indicator values
        latest = merged_df.iloc[-1]
        sma = latest['SMA_tecl']
        wma = latest['WMA_vix']
        
        logger.info(f"TECL: ${tecl_price:.2f}, SMA: ${sma:.2f}, VIX: ${vix_price:.2f}, WMA: ${wma:.2f}")
        
        # Check sell criteria first
        if self.in_position and tecl_price >= self.purchase_price * 1.058:
            self.sell_tecl(tecl_price)
            return
        
        # Skip buy signals if we sold today
        if (self.last_sell_date and 
            self.last_sell_date == datetime.now().date()):
            logger.info("Skipping buy signals - sold today")
            return
        
        # Check buy criteria
        if not self.in_position:
            # Immediate buy if TECL < 0.75 * SMA
            if tecl_price < 0.75 * sma:
                self.buy_tecl(tecl_price, "immediate low TECL")
                return
            
            # VIX condition buy
            if tecl_price < 1.25 * sma:
                # Check VIX condition from 4 days ago
                if len(merged_df) >= 5:
                    prev_vix = merged_df.iloc[-5]['OPEN_vix']
                    prev_wma = merged_df.iloc[-5]['WMA_vix']
                    
                    if prev_vix > 1.04 * prev_wma:
                        self.buy_tecl(tecl_price, "VIX condition met")
    
    def run_trading_session(self) -> None:
        """Run a single trading session check."""
        logger.info("Starting trading session...")
        
        try:
            # Check if market is open
            clock = self.trading_client.get_clock()
            if not clock.is_open:
                logger.info("Market is closed")
                return
            
            # Check account status
            account_info = self.get_account_info()
            logger.info(f"Account value: ${account_info['portfolio_value']:,.2f}")
            
            # Check trading signals
            self.check_trading_signals()
            
        except Exception as e:
            logger.error(f"Error in trading session: {e}")
        
        logger.info("Trading session completed")


def main():
    """Main entry point for live trading."""
    trader = AlpacaLiveTrader()
    trader.run_trading_session()


if __name__ == "__main__":
    main()