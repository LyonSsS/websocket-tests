import jsonschema
from typing import Dict, List, Any
from datetime import datetime


def validate_schema(message: Dict, schema: Dict) -> None:
    """
    Validate message against JSON schema.

    Args:
        message: Message to validate
        schema: JSON schema

    Raises:
        jsonschema.ValidationError: If validation fails
    """
    jsonschema.validate(instance=message, schema=schema)


def validate_timestamp(timestamp: Any, allow_future: bool = False) -> bool:
    """
    Validate timestamp format and value.

    Args:
        timestamp: Timestamp value (float or string)
        allow_future: Whether to allow future timestamps

    Returns:
        True if valid

    Raises:
        ValueError: If timestamp is invalid
    """
    try:
        if isinstance(timestamp, str):
            ts = float(timestamp)
        else:
            ts = float(timestamp)

        if ts <= 0:
            raise ValueError(f"Timestamp must be positive: {ts}")

        if not allow_future:
            now = datetime.now().timestamp()
            if ts > now + 60:  # Allow 60 second clock skew
                raise ValueError(f"Timestamp is too far in future: {ts}")

        return True
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid timestamp: {timestamp} - {e}")


def validate_timestamps_increasing(timestamps: List[float]) -> bool:
    """
    Validate that timestamps are strictly increasing.

    Args:
        timestamps: List of timestamp values

    Returns:
        True if strictly increasing

    Raises:
        ValueError: If timestamps are not increasing
    """
    for i in range(1, len(timestamps)):
        if timestamps[i] <= timestamps[i-1]:
            raise ValueError(
                f"Timestamps not strictly increasing: "
                f"{timestamps[i-1]} >= {timestamps[i]} at index {i}"
            )
    return True


def validate_book_not_crossed(bids: List, asks: List) -> bool:
    """
    Validate that order book is not crossed.

    Args:
        bids: List of bid entries [price, volume, ...]
        asks: List of ask entries [price, volume, ...]

    Returns:
        True if book is not crossed

    Raises:
        ValueError: If book is crossed
    """
    if not bids or not asks:
        return True  # Empty book is not crossed

    best_bid = float(bids[0][0])
    best_ask = float(asks[0][0])

    if best_bid >= best_ask:
        raise ValueError(
            f"Order book is crossed: best_bid={best_bid} >= best_ask={best_ask}"
        )

    return True


def validate_price_ordering(prices: List[float], descending: bool = True) -> bool:
    """
    Validate that prices are in correct order.

    Args:
        prices: List of prices
        descending: True for descending order (bids), False for ascending (asks)

    Returns:
        True if correctly ordered

    Raises:
        ValueError: If prices are not correctly ordered
    """
    for i in range(1, len(prices)):
        if descending:
            if prices[i] > prices[i-1]:
                raise ValueError(
                    f"Prices not in descending order: "
                    f"{prices[i-1]} < {prices[i]} at index {i}"
                )
        else:
            if prices[i] < prices[i-1]:
                raise ValueError(
                    f"Prices not in ascending order: "
                    f"{prices[i-1]} > {prices[i]} at index {i}"
                )
    return True


def validate_ohlc_relationships(open_price: float, high: float, low: float, close: float) -> bool:
    """
    Validate OHLC mathematical relationships.

    Args:
        open_price: Opening price
        high: High price
        low: Low price
        close: Closing price

    Returns:
        True if relationships are valid

    Raises:
        ValueError: If OHLC relationships are invalid
    """
    if low > open_price:
        raise ValueError(f"Low ({low}) > Open ({open_price})")
    if low > close:
        raise ValueError(f"Low ({low}) > Close ({close})")
    if low > high:
        raise ValueError(f"Low ({low}) > High ({high})")

    if high < open_price:
        raise ValueError(f"High ({high}) < Open ({open_price})")
    if high < close:
        raise ValueError(f"High ({high}) < Close ({close})")

    return True


def validate_positive(value: float, field_name: str = "value") -> bool:
    """
    Validate that a numeric value is positive.

    Args:
        value: Value to validate
        field_name: Field name for error message

    Returns:
        True if positive

    Raises:
        ValueError: If value is not positive
    """
    if value <= 0:
        raise ValueError(f"{field_name} must be positive: {value}")
    return True
