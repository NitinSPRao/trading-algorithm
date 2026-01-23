"""Live trading implementation using Alpaca API."""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import time

import pandas as pd
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from dotenv import load_dotenv
import yfinance as yf

from .backtesting import calculate_indicators
from .dynamodb_handler import DynamoDBHandler

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

        # Initialize DynamoDB handler
        self.db = DynamoDBHandler()

        # Trading state
        self.in_position = False
        self.purchase_price = None
        self.purchase_date = None
        self.position_size = 0
        self.last_sell_date = None

        # Configuration
        self.position_size_limit = float(os.getenv('POSITION_SIZE_LIMIT', 0.95))

        # Sync position state with Alpaca and DynamoDB
        self._sync_position_state()

        logger.info("AlpacaLiveTrader initialized successfully")
    
    def _load_state(self) -> Optional[Dict[str, Any]]:
        """Load trading state from DynamoDB."""
        try:
            state = self.db.load_state(trader_id="main")
            if state:
                logger.info("Loaded state from DynamoDB")
                return state
        except Exception as e:
            logger.warning(f"Error loading state from DynamoDB: {e}")
        return None

    def _save_state(self) -> None:
        """Save current trading state to DynamoDB."""
        try:
            success = self.db.save_state(
                in_position=self.in_position,
                purchase_price=self.purchase_price,
                purchase_date=self.purchase_date.isoformat() if self.purchase_date else None,
                position_size=self.position_size,
                last_sell_date=self.last_sell_date.isoformat() if isinstance(self.last_sell_date, datetime) else str(self.last_sell_date) if self.last_sell_date else None,
                trader_id="main"
            )

            if success:
                logger.info("Saved state to DynamoDB")
            else:
                logger.error("Failed to save state to DynamoDB")

        except Exception as e:
            logger.error(f"Error saving state to DynamoDB: {e}")

    def _sync_position_state(self) -> None:
        """Sync position state with Alpaca on initialization."""
        try:
            # First, try to load state from file
            saved_state = self._load_state()

            # Then check Alpaca for current positions
            positions = self.trading_client.get_all_positions()

            # Check if we have a TECL position
            tecl_position = None
            for position in positions:
                if position.symbol == 'TECL':
                    tecl_position = position
                    break

            if tecl_position:
                # We have a position in Alpaca
                self.in_position = True
                self.position_size = int(tecl_position.qty)
                self.purchase_price = float(tecl_position.avg_entry_price)

                # Try to restore purchase_date from saved state
                if saved_state and saved_state.get('in_position') and saved_state.get('purchase_date'):
                    try:
                        self.purchase_date = datetime.fromisoformat(saved_state['purchase_date'])
                        logger.info(f"Restored purchase_date from state: {self.purchase_date}")
                    except Exception as e:
                        logger.warning(f"Error parsing purchase_date from state: {e}")
                        self.purchase_date = datetime.now()
                        logger.warning("Using current date as purchase_date fallback")
                else:
                    # No saved state with purchase date
                    self.purchase_date = datetime.now()
                    logger.warning("No saved purchase_date found, using current date as fallback")

                logger.info(f"Synced existing TECL position: {self.position_size} shares at ${self.purchase_price:.2f}, purchased on {self.purchase_date}")

            else:
                # No position in Alpaca
                logger.info("No existing TECL position found")

                # Restore last_sell_date from saved state if available
                if saved_state and saved_state.get('last_sell_date'):
                    try:
                        self.last_sell_date = datetime.fromisoformat(saved_state['last_sell_date']).date()
                        logger.info(f"Restored last_sell_date from state: {self.last_sell_date}")
                    except Exception as e:
                        logger.warning(f"Error parsing last_sell_date from state: {e}")

        except Exception as e:
            logger.warning(f"Error syncing position state: {e}")
            # Continue with default state (no position)

    def get_account_info(self) -> dict[str, Any]:
        """Get current account information."""
        account = self.trading_client.get_account()
        return {
            'buying_power': float(account.buying_power),
            'portfolio_value': float(account.portfolio_value),
            'cash': float(account.cash),
            'day_trade_buying_power': float(getattr(account, 'day_trade_buying_power', account.buying_power))
        }
    
    def get_current_price(self, symbol: str, max_retries: int = 3) -> Optional[float]:
        """Get current price for a symbol with retry logic and exponential backoff."""
        yf_symbol = '^VIX' if symbol == 'VIX' else symbol

        for attempt in range(max_retries):
            try:
                logger.info(f"Fetching current price for {symbol} (attempt {attempt + 1}/{max_retries})")

                # Add delay between requests to avoid rate limiting
                if attempt == 0:
                    time.sleep(2)  # 2 second delay before first request

                ticker = yf.Ticker(yf_symbol)

                # Try current day first
                hist = ticker.history(period='1d')

                # If no data for current day, try last 2 days (handles pre-market/early trading)
                if hist.empty:
                    logger.warning(f"No 1d data for {symbol}, trying 2d period")
                    time.sleep(3)  # Extra delay before retry
                    hist = ticker.history(period='2d')

                if not hist.empty:
                    price = float(hist['Close'].iloc[-1])
                    logger.info(f"Successfully fetched {symbol} price: ${price:.2f}")
                    return price
                else:
                    logger.warning(f"No historical data available for {symbol} on attempt {attempt + 1}")

            except Exception as e:
                error_msg = str(e)
                is_rate_limit = 'rate limit' in error_msg.lower() or 'too many requests' in error_msg.lower()

                if is_rate_limit:
                    logger.warning(f"Rate limited on attempt {attempt + 1} for {symbol}")
                else:
                    logger.error(f"Error getting price for {symbol} on attempt {attempt + 1}: {e}", exc_info=False)

                # Exponential backoff for rate limits: 15s, 45s, 90s
                if attempt < max_retries - 1:
                    wait_time = 15 * (3 ** attempt) if is_rate_limit else 10
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)

        logger.error(f"Failed to fetch price for {symbol} after {max_retries} attempts")
        return None
    
    def get_historical_data(self, symbol: str, days: int = 60, max_retries: int = 3) -> pd.DataFrame:
        """Get historical data for indicator calculations with retry logic and exponential backoff."""
        yf_symbol = '^VIX' if symbol == 'VIX' else symbol

        for attempt in range(max_retries):
            try:
                logger.info(f"Fetching historical data for {symbol} ({days} days, attempt {attempt + 1}/{max_retries})")

                # Add delay between requests to avoid rate limiting
                if attempt == 0:
                    time.sleep(3)  # 3 second delay before first request

                ticker = yf.Ticker(yf_symbol)
                hist = ticker.history(period=f'{days}d')

                if not hist.empty:
                    logger.info(f"Successfully fetched {len(hist)} rows of historical data for {symbol}")
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
                    logger.warning(f"No historical data found for {symbol} on attempt {attempt + 1}")

            except Exception as e:
                error_msg = str(e)
                is_rate_limit = 'rate limit' in error_msg.lower() or 'too many requests' in error_msg.lower()

                if is_rate_limit:
                    logger.warning(f"Rate limited on attempt {attempt + 1} for {symbol}")
                else:
                    logger.error(f"Error getting historical data for {symbol} on attempt {attempt + 1}: {e}", exc_info=False)

                # Exponential backoff for rate limits: 20s, 60s, 120s
                if attempt < max_retries - 1:
                    wait_time = 20 * (3 ** attempt) if is_rate_limit else 10
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)

        logger.error(f"Failed to fetch historical data for {symbol} after {max_retries} attempts")
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
            self.purchase_date = datetime.now()
            self.position_size = shares
            logger.info(f"BUY: {shares} shares of TECL at ${price:.2f} - {reason}")

            # Save state after successful purchase
            self._save_state()

            # Log buy event to DynamoDB
            self.db.log_event(
                event_type="BUY",
                symbol="TECL",
                price=price,
                quantity=shares,
                success=True,
                details={"reason": reason, "buying_power_used_pct": self.position_size_limit}
            )

            return True
        return False
    
    def sell_tecl(self, price: float) -> bool:
        """Execute a sell order for TECL."""
        if not self.in_position:
            logger.warning("Not in position, skipping sell signal")
            return False
        
        if self.place_order('TECL', OrderSide.SELL, self.position_size):
            profit_pct = (price / self.purchase_price - 1) * 100
            profit_dollars = (price - self.purchase_price) * self.position_size
            logger.info(f"SELL: {self.position_size} shares of TECL at ${price:.2f} - Profit: {profit_pct:.2f}%")

            # Log sell event to DynamoDB before clearing state
            self.db.log_event(
                event_type="SELL",
                symbol="TECL",
                price=price,
                quantity=self.position_size,
                success=True,
                details={
                    "purchase_price": self.purchase_price,
                    "profit_pct": profit_pct,
                    "profit_dollars": profit_dollars,
                    "hold_days": (datetime.now() - self.purchase_date).days if self.purchase_date else None
                }
            )

            self.in_position = False
            self.purchase_price = None
            self.purchase_date = None
            self.position_size = 0
            self.last_sell_date = datetime.now().date()

            # Save state after successful sale
            self._save_state()

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

        # Log signal check event
        self.db.log_event(
            event_type="SIGNAL_CHECK",
            symbol="TECL",
            price=tecl_price,
            vix=vix_price,
            sma_tecl=sma,
            wma_vix=wma,
            details={
                "in_position": self.in_position,
                "purchase_price": self.purchase_price,
                "position_size": self.position_size
            }
        )

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