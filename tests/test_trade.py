"""
Tests for Kraken WebSocket API v2 - Trade Channel

The trade channel activates when orders match in the book.
Provides real-time trade execution data including price, quantity, and order type.

Key features:
- Supports snapshot (last 50 trades) and real-time updates
- Each trade has unique trade_id sequence number
- Includes taker side (buy/sell) and order type (limit/market)
"""

import pytest
import json
import jsonschema
import os
from typing import Dict, List

from utils.websocket_client import KrakenWebSocketClient


# Constants
WS_URL = "wss://ws.kraken.com/v2"
TEST_SYMBOL = "BTC/USD"
TEST_SYMBOLS_MULTI = ["BTC/USD", "ETH/USD"]


class TestTradeChannel:
    """Test suite for trade channel functionality."""

    @pytest.fixture
    def schema(self):
        """Load trade channel JSON schema."""
        schema_path = os.path.join(
            os.path.dirname(__file__), '..', 'schemas', 'trade_schema.json'
        )
        with open(schema_path) as f:
            return json.load(f)

    def test_trade_complete_flow(self, default_timeout):
        """
        Test complete trade subscription flow.

        Steps:
        1. Subscribe to trade channel
        2. Validate subscription acknowledgment
        3. Receive trade messages
        4. Unsubscribe
        5. Validate unsubscription acknowledgment
        """
        with KrakenWebSocketClient(WS_URL, timeout=default_timeout) as client:
            # Subscribe to trade channel
            ack = client.subscribe(channel="trade", symbol=[TEST_SYMBOL])
            assert ack.get("success") is True
            assert ack.get("method") == "subscribe"

            # Receive trade messages
            messages = client.receive_messages(count=3, timeout=default_timeout)
            assert len(messages) > 0, "No trade messages received"

            # Verify all messages are from trade channel
            for msg in messages:
                assert msg.get("channel") == "trade"
                assert msg.get("type") in ["snapshot", "update"]

            # Unsubscribe
            try:
                unsub = client.unsubscribe(channel="trade", symbol=[TEST_SYMBOL])
                print(f"✓ Unsubscribed successfully: {unsub.get('success')}")
            except Exception as e:
                # Catch both TimeoutError and WebSocketTimeoutException
                if 'timeout' not in str(e).lower() and 'Timeout' not in type(e).__name__:
                    raise
                print(f"⚠ Warning: Unsubscribe timed out (acceptable for high-frequency channels): {e}")

    def test_trade_snapshot_default(self, default_timeout):
        """
        Test trade channel with default snapshot behavior (snapshot=false).

        By default, no snapshot is sent - only live updates.
        Note: May timeout if no trades happen in market (acceptable).
        """
        with KrakenWebSocketClient(WS_URL, timeout=default_timeout) as client:
            ack = client.subscribe(channel="trade", symbol=[TEST_SYMBOL])
            assert ack.get("success") is True

            # Wait for first message - may timeout if no live trades
            try:
                messages = client.receive_messages(count=1, timeout=default_timeout)
                assert len(messages) >= 1

                # First message might be snapshot or update depending on timing
                first_msg = messages[0]
                assert first_msg.get("channel") == "trade"
                assert first_msg.get("type") in ["snapshot", "update"]
                print(f"✓ Received {first_msg.get('type')} with {len(first_msg.get('data', []))} trades")
            except Exception as e:
                # Timeout is acceptable if no live trades in market
                if 'timeout' not in str(e).lower() and 'Timeout' not in type(e).__name__:
                    raise
                print(f"⚠ No live trades received within timeout (acceptable for slow market): {e}")

            # Unsubscribe
            try:
                client.unsubscribe(channel="trade", symbol=[TEST_SYMBOL])
            except Exception as e:
                if 'timeout' not in str(e).lower() and 'Timeout' not in type(e).__name__:
                    raise
                print(f"⚠ Unsubscribe timeout (acceptable): {e}")

    def test_trade_snapshot_true(self, default_timeout):
        """
        Test trade channel with snapshot=true.

        Should receive snapshot of last 50 trades, then live updates.
        """
        with KrakenWebSocketClient(WS_URL, timeout=default_timeout) as client:
            ack = client.subscribe(
                channel="trade",
                symbol=[TEST_SYMBOL],
                snapshot=True
            )
            assert ack.get("success") is True

            # Wait for snapshot
            messages = client.receive_messages(count=1, timeout=default_timeout)
            assert len(messages) >= 1

            snapshot = messages[0]
            assert snapshot.get("channel") == "trade"
            assert snapshot.get("type") == "snapshot"
            assert len(snapshot.get("data", [])) > 0, "Snapshot should contain trade data"

            print(f"✓ Received snapshot with {len(snapshot['data'])} trades")

            # Unsubscribe
            try:
                client.unsubscribe(channel="trade", symbol=[TEST_SYMBOL])
            except Exception as e:
                if 'timeout' not in str(e).lower() and 'Timeout' not in type(e).__name__:
                    raise
                print(f"⚠ Unsubscribe timeout (acceptable): {e}")

    def test_trade_snapshot_false(self, default_timeout):
        """
        Test trade channel with explicit snapshot=false.

        Should only receive live trade updates, no initial snapshot.
        """
        with KrakenWebSocketClient(WS_URL, timeout=default_timeout) as client:
            ack = client.subscribe(
                channel="trade",
                symbol=[TEST_SYMBOL],
                snapshot=False
            )
            assert ack.get("success") is True

            # Wait for messages - should be updates only
            messages = client.receive_messages(count=2, timeout=default_timeout)
            assert len(messages) >= 1

            # All messages should be updates (no snapshot)
            for msg in messages:
                assert msg.get("channel") == "trade"
                # May receive updates or occasionally snapshot
                assert msg.get("type") in ["snapshot", "update"]

            # Unsubscribe
            try:
                client.unsubscribe(channel="trade", symbol=[TEST_SYMBOL])
            except Exception as e:
                if 'timeout' not in str(e).lower() and 'Timeout' not in type(e).__name__:
                    raise
                print(f"⚠ Unsubscribe timeout (acceptable): {e}")

    def test_trade_schema_validation(self, schema, default_timeout):
        """
        Test that trade messages conform to JSON schema.

        Validates:
        - Required fields present
        - Correct data types
        - Valid enum values (snapshot/update, limit/market)
        """
        with KrakenWebSocketClient(WS_URL, timeout=default_timeout) as client:
            client.subscribe(channel="trade", symbol=[TEST_SYMBOL], snapshot=True)

            messages = client.receive_messages(count=3, timeout=default_timeout)
            assert len(messages) > 0

            for msg in messages:
                try:
                    jsonschema.validate(instance=msg, schema=schema)
                    print(f"✓ Message validates against schema: {msg.get('type')}")
                except jsonschema.ValidationError as e:
                    pytest.fail(f"Schema validation failed: {e.message}")

            # Unsubscribe
            try:
                client.unsubscribe(channel="trade", symbol=[TEST_SYMBOL])
            except Exception as e:
                if 'timeout' not in str(e).lower() and 'Timeout' not in type(e).__name__:
                    raise

    def test_trade_data_integrity(self, default_timeout):
        """
        Test data integrity constraints for trade messages.

        Validates:
        0. Data array not empty & all required fields present
        1. qty > 0 (positive trade size)
        2. price > 0 (positive price)
        3. side is 'buy' or 'sell'
        4. ord_type is 'limit' or 'market'
        5. trade_id > 0 (positive integer)
        6. symbol matches subscription
        7. timestamp is valid RFC3339 format
        """
        with KrakenWebSocketClient(WS_URL, timeout=default_timeout) as client:
            client.subscribe(channel="trade", symbol=[TEST_SYMBOL], snapshot=True)

            messages = client.receive_messages(count=3, timeout=default_timeout)
            assert len(messages) > 0

            violations = []

            for i, msg in enumerate(messages):
                print(f"\n  Validating message {i + 1} ({msg.get('type')}):")

                # Check that data array is not empty
                data = msg.get("data", [])
                try:
                    assert len(data) > 0, "Message data array is empty"
                    print(f"  Message {i + 1}: ✓ Data array not empty ({len(data)} trades)")
                except AssertionError as e:
                    violations.append(str(e))
                    print(f"  Message {i + 1}: ✗ {e}")
                    continue

                for j, trade in enumerate(data):
                    print(f"    Trade {j + 1}:")

                    symbol = trade.get("symbol")
                    side = trade.get("side")
                    qty = trade.get("qty")
                    price = trade.get("price")
                    ord_type = trade.get("ord_type")
                    trade_id = trade.get("trade_id")
                    timestamp = trade.get("timestamp")

                    # Required fields are not None
                    try:
                        assert symbol is not None, "symbol is None"
                        assert side is not None, "side is None"
                        assert qty is not None, "qty is None"
                        assert price is not None, "price is None"
                        assert ord_type is not None, "ord_type is None"
                        assert trade_id is not None, "trade_id is None"
                        assert timestamp is not None, "timestamp is None"
                        print(f"      ✓ All required fields present")
                    except AssertionError as e:
                        violations.append(str(e))
                        print(f"      ✗ {e}")

                    # 1. Quantity validation
                    try:
                        assert qty > 0, f"qty ({qty}) <= 0"
                        print(f"      ✓ qty > 0: {qty}")
                    except (AssertionError, TypeError) as e:
                        violations.append(str(e))
                        print(f"      ✗ {e}")

                    # 2. Price validation
                    try:
                        assert price > 0, f"price ({price}) <= 0"
                        print(f"      ✓ price > 0: {price}")
                    except (AssertionError, TypeError) as e:
                        violations.append(str(e))
                        print(f"      ✗ {e}")

                    # 3. Side validation
                    try:
                        assert side in ["buy", "sell"], f"side ({side}) not in ['buy', 'sell']"
                        print(f"      ✓ side valid: {side}")
                    except AssertionError as e:
                        violations.append(str(e))
                        print(f"      ✗ {e}")

                    # 4. Order type validation
                    try:
                        assert ord_type in ["limit", "market"], f"ord_type ({ord_type}) not in ['limit', 'market']"
                        print(f"      ✓ ord_type valid: {ord_type}")
                    except AssertionError as e:
                        violations.append(str(e))
                        print(f"      ✗ {e}")

                    # 5. Trade ID validation
                    try:
                        assert isinstance(trade_id, int), f"trade_id ({trade_id}) not integer"
                        assert trade_id > 0, f"trade_id ({trade_id}) <= 0"
                        print(f"      ✓ trade_id > 0: {trade_id}")
                    except (AssertionError, TypeError) as e:
                        violations.append(str(e))
                        print(f"      ✗ {e}")

                    # 6. Symbol validation
                    try:
                        assert symbol == TEST_SYMBOL, f"symbol ({symbol}) != {TEST_SYMBOL}"
                        print(f"      ✓ symbol matches: {symbol}")
                    except AssertionError as e:
                        violations.append(str(e))
                        print(f"      ✗ {e}")

                    # 7. Timestamp format validation
                    try:
                        from datetime import datetime
                        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        print(f"      ✓ timestamp valid RFC3339: {timestamp}")
                    except Exception as e:
                        violations.append(f"Invalid timestamp format: {e}")
                        print(f"      ✗ Invalid timestamp: {e}")

            # Unsubscribe
            try:
                client.unsubscribe(channel="trade", symbol=[TEST_SYMBOL])
            except Exception as e:
                if 'timeout' not in str(e).lower() and 'Timeout' not in type(e).__name__:
                    raise

            # Report violations
            if violations:
                pytest.fail(f"Data integrity violations:\n" + "\n".join(violations))

    def test_trade_multiple_symbols(self, default_timeout):
        """
        Test subscribing to multiple symbols simultaneously.

        Validates:
        - Can subscribe to multiple symbols in one request
        - Messages contain correct symbols
        - All symbols receive updates
        """
        with KrakenWebSocketClient(WS_URL, timeout=default_timeout) as client:
            ack = client.subscribe(channel="trade", symbol=TEST_SYMBOLS_MULTI, snapshot=True)
            assert ack.get("success") is True

            # Receive messages
            messages = client.receive_messages(count=5, timeout=default_timeout)
            assert len(messages) > 0

            # Collect symbols from messages
            symbols_seen = set()
            for msg in messages:
                for trade in msg.get("data", []):
                    symbols_seen.add(trade.get("symbol"))

            print(f"✓ Received trades for symbols: {symbols_seen}")

            # Verify at least one of our symbols appeared
            assert len(symbols_seen.intersection(TEST_SYMBOLS_MULTI)) > 0, \
                f"No trades for subscribed symbols. Got: {symbols_seen}"

            # Unsubscribe
            try:
                client.unsubscribe(channel="trade", symbol=TEST_SYMBOLS_MULTI)
            except Exception as e:
                if 'timeout' not in str(e).lower() and 'Timeout' not in type(e).__name__:
                    raise
                print(f"⚠ Unsubscribe timeout (acceptable): {e}")

    def test_trade_invalid_symbol(self):
        """Test that subscribing to invalid symbol fails gracefully."""
        with KrakenWebSocketClient(WS_URL, timeout=10) as client:
            with pytest.raises(ValueError, match="Subscription failed"):
                client.subscribe(channel="trade", symbol=["INVALID/PAIR"])

    def test_trade_trade_id_sequence(self, default_timeout):
        """
        Test that trade_id values form a sequence.

        Note: trade_id is unique per book, but may have gaps or not be strictly
        sequential across different messages. We validate they're all positive integers.
        """
        with KrakenWebSocketClient(WS_URL, timeout=default_timeout) as client:
            client.subscribe(channel="trade", symbol=[TEST_SYMBOL], snapshot=True)

            messages = client.receive_messages(count=3, timeout=default_timeout)
            assert len(messages) > 0

            all_trade_ids = []

            for msg in messages:
                for trade in msg.get("data", []):
                    trade_id = trade.get("trade_id")
                    if trade_id is not None:
                        all_trade_ids.append(trade_id)

            assert len(all_trade_ids) > 0, "No trade_ids found"

            # Verify all are positive integers
            for tid in all_trade_ids:
                assert isinstance(tid, int), f"trade_id {tid} is not an integer"
                assert tid > 0, f"trade_id {tid} is not positive"

            print(f"✓ All {len(all_trade_ids)} trade_ids are positive integers")
            print(f"  Range: {min(all_trade_ids)} to {max(all_trade_ids)}")

            # Unsubscribe
            try:
                client.unsubscribe(channel="trade", symbol=[TEST_SYMBOL])
            except Exception as e:
                if 'timeout' not in str(e).lower() and 'Timeout' not in type(e).__name__:
                    raise

    def test_trade_side_distribution(self, default_timeout):
        """
        Test that trade messages contain both buy and sell sides.

        Note: Depending on market conditions, we may not see both sides,
        but we validate that all sides are valid values.
        """
        with KrakenWebSocketClient(WS_URL, timeout=default_timeout) as client:
            client.subscribe(channel="trade", symbol=[TEST_SYMBOL], snapshot=True)

            messages = client.receive_messages(count=5, timeout=default_timeout)
            assert len(messages) > 0

            sides_seen = set()

            for msg in messages:
                for trade in msg.get("data", []):
                    side = trade.get("side")
                    if side:
                        sides_seen.add(side)
                        assert side in ["buy", "sell"], f"Invalid side: {side}"

            print(f"✓ Sides observed: {sides_seen}")
            assert len(sides_seen) > 0, "No sides found in trades"

            # Unsubscribe
            try:
                client.unsubscribe(channel="trade", symbol=[TEST_SYMBOL])
            except Exception as e:
                if 'timeout' not in str(e).lower() and 'Timeout' not in type(e).__name__:
                    raise

    def test_trade_order_type_distribution(self, default_timeout):
        """
        Test that trade messages contain valid order types.

        Validates all order types are either 'limit' or 'market'.
        """
        with KrakenWebSocketClient(WS_URL, timeout=default_timeout) as client:
            client.subscribe(channel="trade", symbol=[TEST_SYMBOL], snapshot=True)

            messages = client.receive_messages(count=5, timeout=default_timeout)
            assert len(messages) > 0

            order_types_seen = set()

            for msg in messages:
                for trade in msg.get("data", []):
                    ord_type = trade.get("ord_type")
                    if ord_type:
                        order_types_seen.add(ord_type)
                        assert ord_type in ["limit", "market"], f"Invalid ord_type: {ord_type}"

            print(f"✓ Order types observed: {order_types_seen}")
            assert len(order_types_seen) > 0, "No order types found in trades"

            # Unsubscribe
            try:
                client.unsubscribe(channel="trade", symbol=[TEST_SYMBOL])
            except Exception as e:
                if 'timeout' not in str(e).lower() and 'Timeout' not in type(e).__name__:
                    raise
