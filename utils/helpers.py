import json
from typing import Dict, List, Any, Optional
from pathlib import Path


def parse_channel_message(message: Any) -> Optional[Dict]:
    """
    Parse channel data message.

    Kraken sends channel data as arrays: [channelID, data, channelName, pair]

    Args:
        message: Raw message from WebSocket

    Returns:
        Parsed message dict or None if not a channel message
    """
    if isinstance(message, list) and len(message) >= 4:
        return {
            "channel_id": message[0],
            "data": message[1],
            "channel_name": message[2],
            "pair": message[3]
        }
    return None


def is_system_message(message: Any) -> bool:
    """
    Check if message is a system/event message.

    Args:
        message: Message to check

    Returns:
        True if system message
    """
    return isinstance(message, dict) and "event" in message


def extract_ticker_data(message: Dict) -> Optional[Dict]:
    """
    Extract ticker data from channel message.

    Args:
        message: Parsed channel message

    Returns:
        Ticker data dict or None
    """
    if message.get("channel_name") != "ticker":
        return None

    data = message.get("data", {})
    return {
        "ask": data.get("a", []),
        "bid": data.get("b", []),
        "close": data.get("c", []),
        "volume": data.get("v", []),
        "vwap": data.get("p", []),
        "trades": data.get("t", []),
        "low": data.get("l", []),
        "high": data.get("h", []),
        "open": data.get("o", [])
    }


def extract_book_data(message: Dict) -> Optional[Dict]:
    """
    Extract order book data from channel message.

    Args:
        message: Parsed channel message

    Returns:
        Book data dict or None
    """
    channel_name = message.get("channel_name", "")
    if not channel_name.startswith("book"):
        return None

    data = message.get("data", {})

    # Handle snapshot vs update
    if "as" in data and "bs" in data:
        # Snapshot
        return {
            "type": "snapshot",
            "asks": data["as"],
            "bids": data["bs"]
        }
    else:
        # Update
        return {
            "type": "update",
            "asks": data.get("a", []),
            "bids": data.get("b", [])
        }


def extract_ohlc_data(message: Dict) -> Optional[Dict]:
    """
    Extract OHLC/candles data from channel message.

    Args:
        message: Parsed channel message

    Returns:
        OHLC data dict or None
    """
    channel_name = message.get("channel_name", "")
    if not channel_name.startswith("ohlc"):
        return None

    data = message.get("data", [])
    if len(data) >= 8:
        return {
            "time": float(data[0]),
            "etime": float(data[1]),
            "open": float(data[2]),
            "high": float(data[3]),
            "low": float(data[4]),
            "close": float(data[5]),
            "vwap": float(data[6]),
            "volume": float(data[7]),
            "count": int(data[8]) if len(data) > 8 else None
        }
    return None


def extract_trades_data(message: Dict) -> Optional[List[Dict]]:
    """
    Extract trades data from channel message.

    Args:
        message: Parsed channel message

    Returns:
        List of trade dicts or None
    """
    channel_name = message.get("channel_name", "")
    if not channel_name.startswith("trade"):
        return None

    data = message.get("data", [])
    trades = []

    for trade in data:
        if len(trade) >= 6:
            trades.append({
                "price": float(trade[0]),
                "volume": float(trade[1]),
                "time": float(trade[2]),
                "side": trade[3],  # 'b' for buy, 's' for sell
                "order_type": trade[4],  # 'l' for limit, 'm' for market
                "misc": trade[5]
            })

    return trades if trades else None


def save_message_to_fixture(message: Any, filename: str, fixtures_dir: str = "fixtures") -> None:
    """
    Save a message to fixtures directory for future replay.

    Args:
        message: Message to save
        filename: Filename (without path)
        fixtures_dir: Fixtures directory path
    """
    fixtures_path = Path(fixtures_dir)
    fixtures_path.mkdir(exist_ok=True)

    filepath = fixtures_path / filename
    with open(filepath, 'w') as f:
        json.dump(message, f, indent=2)


def load_message_from_fixture(filename: str, fixtures_dir: str = "fixtures") -> Any:
    """
    Load a message from fixtures directory.

    Args:
        filename: Filename (without path)
        fixtures_dir: Fixtures directory path

    Returns:
        Loaded message
    """
    filepath = Path(fixtures_dir) / filename
    with open(filepath, 'r') as f:
        return json.load(f)
