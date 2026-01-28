"""DynamoDB handler for trading state and event logging."""
import os
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class DynamoDBHandler:
    """Handles all DynamoDB operations for trading state and event logging."""

    def __init__(
        self,
        region: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        state_table: Optional[str] = None,
        events_table: Optional[str] = None,
    ):
        """
        Initialize DynamoDB handler.

        Args:
            region: AWS region (defaults to env var AWS_REGION)
            access_key: AWS access key (defaults to env var AWS_ACCESS_KEY_ID)
            secret_key: AWS secret key (defaults to env var AWS_SECRET_ACCESS_KEY)
            state_table: State table name (defaults to env var DYNAMODB_STATE_TABLE)
            events_table: Events table name (defaults to env var DYNAMODB_EVENTS_TABLE)
        """
        self.region = region or os.getenv("AWS_REGION", "us-east-2")
        self.access_key = access_key or os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_key = secret_key or os.getenv("AWS_SECRET_ACCESS_KEY")
        self.state_table_name = state_table or os.getenv("DYNAMODB_STATE_TABLE", "trading_state")
        self.events_table_name = events_table or os.getenv(
            "DYNAMODB_EVENTS_TABLE", "trading_events"
        )

        # Initialize DynamoDB client
        self.dynamodb = boto3.resource(
            "dynamodb",
            region_name=self.region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )

        self.state_table = self.dynamodb.Table(self.state_table_name)
        self.events_table = self.dynamodb.Table(self.events_table_name)

        logger.info(
            f"DynamoDB handler initialized (region={self.region}, "
            f"state_table={self.state_table_name}, events_table={self.events_table_name})"
        )

    def _convert_floats_to_decimal(self, obj: Any) -> Any:
        """Convert float values to Decimal for DynamoDB compatibility."""
        if isinstance(obj, float):
            return Decimal(str(obj))
        elif isinstance(obj, dict):
            return {k: self._convert_floats_to_decimal(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_floats_to_decimal(item) for item in obj]
        return obj

    def _convert_decimal_to_float(self, obj: Any) -> Any:
        """Convert Decimal values back to float for Python compatibility."""
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: self._convert_decimal_to_float(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_decimal_to_float(item) for item in obj]
        return obj

    # ========== STATE MANAGEMENT ==========

    def load_state(self, trader_id: str = "main") -> Dict[str, Any]:
        """
        Load trading state from DynamoDB.

        Args:
            trader_id: Unique identifier for this trader instance

        Returns:
            Dictionary containing state or empty dict if not found
        """
        try:
            response = self.state_table.get_item(Key={"trader_id": trader_id})
            if "Item" in response:
                state = self._convert_decimal_to_float(response["Item"])
                # Remove trader_id from returned state
                state.pop("trader_id", None)
                logger.info(f"Loaded state for trader_id={trader_id}: {state}")
                return state
            else:
                logger.info(f"No existing state found for trader_id={trader_id}")
                return {}
        except ClientError as e:
            logger.error(f"Error loading state from DynamoDB: {e}")
            return {}

    def save_state(
        self,
        in_position: bool,
        purchase_price: Optional[float],
        purchase_date: Optional[str],
        position_size: int,
        last_sell_date: Optional[str],
        trader_id: str = "main",
        initial_capital: Optional[float] = None,
    ) -> bool:
        """
        Save trading state to DynamoDB.

        Args:
            in_position: Whether currently holding a position
            purchase_price: Price at which position was purchased
            purchase_date: ISO format datetime of purchase
            position_size: Number of shares held
            last_sell_date: ISO format datetime of last sell
            trader_id: Unique identifier for this trader instance
            initial_capital: Starting account balance (set once at inception)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Load existing state to preserve initial_capital if not provided
            existing_state = self.load_state(trader_id)

            item = {
                "trader_id": trader_id,
                "in_position": in_position,
                "purchase_price": purchase_price,
                "purchase_date": purchase_date,
                "position_size": position_size,
                "last_sell_date": last_sell_date,
                "last_updated": datetime.now().isoformat(),
            }

            # Preserve or set initial_capital
            if initial_capital is not None:
                item["initial_capital"] = initial_capital
            elif "initial_capital" in existing_state:
                item["initial_capital"] = existing_state["initial_capital"]

            # Convert floats to Decimal
            item = self._convert_floats_to_decimal(item)

            self.state_table.put_item(Item=item)
            logger.info(f"Saved state for trader_id={trader_id}")
            return True
        except ClientError as e:
            logger.error(f"Error saving state to DynamoDB: {e}")
            return False

    # ========== EVENT LOGGING ==========

    def log_event(
        self,
        event_type: str,
        symbol: str = "TECL",
        price: Optional[float] = None,
        quantity: Optional[int] = None,
        vix: Optional[float] = None,
        sma_tecl: Optional[float] = None,
        wma_vix: Optional[float] = None,
        signal_triggered: Optional[bool] = None,
        success: Optional[bool] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Log a trading event to DynamoDB.

        Args:
            event_type: Type of event (BUY, SELL, SIGNAL_CHECK, DAILY_REPORT, etc.)
            symbol: Trading symbol
            price: Price at event time
            quantity: Number of shares
            vix: VIX value
            sma_tecl: TECL simple moving average
            wma_vix: VIX weighted moving average
            signal_triggered: Whether a signal was triggered
            success: Whether the operation succeeded
            details: Additional event details (flexible JSON-like data)

        Returns:
            True if successful, False otherwise
        """
        try:
            now = datetime.now()
            item = {
                "event_date": now.strftime("%Y-%m-%d"),
                "timestamp": now.isoformat(),
                "event_type": event_type,
                "symbol": symbol,
            }

            # Add optional fields only if they're not None
            if price is not None:
                item["price"] = price
            if quantity is not None:
                item["quantity"] = quantity
            if vix is not None:
                item["vix"] = vix
            if sma_tecl is not None:
                item["sma_tecl"] = sma_tecl
            if wma_vix is not None:
                item["wma_vix"] = wma_vix
            if signal_triggered is not None:
                item["signal_triggered"] = signal_triggered
            if success is not None:
                item["success"] = success
            if details is not None:
                item["details"] = details

            # Convert floats to Decimal
            item = self._convert_floats_to_decimal(item)

            self.events_table.put_item(Item=item)
            logger.debug(f"Logged {event_type} event to DynamoDB")
            return True
        except ClientError as e:
            logger.error(f"Error logging event to DynamoDB: {e}")
            return False

    def get_events(
        self, event_date: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve events for a specific date.

        Args:
            event_date: Date in YYYY-MM-DD format
            limit: Maximum number of events to return

        Returns:
            List of event dictionaries
        """
        try:
            query_kwargs = {"KeyConditionExpression": Key("event_date").eq(event_date)}

            if limit:
                query_kwargs["Limit"] = limit

            response = self.events_table.query(**query_kwargs)
            events = [self._convert_decimal_to_float(item) for item in response.get("Items", [])]
            logger.info(f"Retrieved {len(events)} events for date={event_date}")
            return events
        except ClientError as e:
            logger.error(f"Error retrieving events from DynamoDB: {e}")
            return []

    def get_recent_events(
        self, event_type: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve recent events (scans the table - use sparingly).

        Args:
            event_type: Optional filter by event type
            limit: Maximum number of events to return

        Returns:
            List of event dictionaries, sorted by timestamp descending
        """
        try:
            scan_kwargs = {"Limit": limit}

            if event_type:
                scan_kwargs["FilterExpression"] = "event_type = :event_type"
                scan_kwargs["ExpressionAttributeValues"] = {":event_type": event_type}

            response = self.events_table.scan(**scan_kwargs)
            events = [self._convert_decimal_to_float(item) for item in response.get("Items", [])]

            # Sort by timestamp descending
            events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

            logger.info(f"Retrieved {len(events)} recent events")
            return events
        except ClientError as e:
            logger.error(f"Error scanning events from DynamoDB: {e}")
            return []
