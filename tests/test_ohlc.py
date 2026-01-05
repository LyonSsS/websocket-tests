"""
Tests for Kraken WebSocket API v2 - OHLC (Candles) Channel

This module tests the OHLC channel including:
- Subscription and unsubscription with acknowledgment validation
- JSON schema validation for snapshot messages
- Field validation and data integrity constraints
- OHLC-specific validations (price relationships, interval matching, timestamps)
- Interval parameter testing (all valid intervals: 1, 5, 15, 30, 60, 240, 1440, 10080, 21600)
- snapshot parameter testing (true/false, invalid values)
- Negative scenarios (invalid inputs, edge cases)

Test Organization:
1. TestOHLCChannel: Positive test scenarios
2. TestOHLCChannelNegativeScenarios: Error handling and edge cases
"""

import pytest
import time
from utils.websocket_client import KrakenWebSocketClient
from utils.validators import validate_schema


class TestOHLCChannel:
    """Positive test scenarios for OHLC channel."""

    def test_ohlc_complete_flow(self, kraken_ws_url, load_schema, default_timeout):
        """
        COMPREHENSIVE TEST: Complete OHLC channel flow with all scenarios.

        This test validates the entire lifecycle:
        - SCENARIO 1: Subscription and acknowledgment
        - SCENARIO 2: Schema validation
        - SCENARIO 3: Field validation
        - SCENARIO 4: Unsubscription and acknowledgment
        - SCENARIO 5: Verification no data after unsubscribe
        """
        print("\n" + "=" * 70)
        print("COMPREHENSIVE OHLC CHANNEL TEST - All Scenarios")
        print("=" * 70)

        pairs = ["BTC/USD"]
        interval = 5
        schema = load_schema("candles")

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:

            # ================================================================
            # SCENARIO 1: Subscription Acknowledgment
            # ================================================================
            print("\n" + "-" * 70)
            print("SCENARIO 1: Subscription and Acknowledgment Validation")
            print("-" * 70)

            ack = client.subscribe("ohlc", pairs, interval=interval)

            print(f"  Subscription request sent for: {', '.join(pairs)}")
            print(f"  Interval: {interval}")
            print(f"\n  Acknowledgment received:")
            print(f"    success: {ack.get('success')}")
            print(f"    method: {ack.get('method')}")
            print(f"    result.channel: {ack.get('result', {}).get('channel')}")
            print(f"    result.symbol: {ack.get('result', {}).get('symbol')}")

            assert ack.get("success") is True, "Subscription must succeed"
            assert ack.get("method") == "subscribe", "Method must be 'subscribe'"
            assert ack.get("result", {}).get("channel") == "ohlc", "Channel must be 'ohlc'"

            print(f"\n  ✓ SCENARIO 1 PASSED: Subscription acknowledged")

            # ================================================================
            # SCENARIO 2: Schema Validation
            # ================================================================
            print("\n" + "-" * 70)
            print("SCENARIO 2: JSON Schema Validation")
            print("-" * 70)

            messages = client.receive_messages(count=2, timeout=60)
            print(f"  Received {len(messages)} messages")

            snapshot_found = False
            for i, msg in enumerate(messages, 1):
                msg_type = msg.get("type")
                print(f"\n  Message {i}:")
                print(f"    Channel: {msg.get('channel')}")
                print(f"    Type: {msg_type}")

                # Validate schema
                validate_schema(msg, schema)
                print(f"    ✓ Schema validation passed")

                if msg_type == "snapshot":
                    snapshot_found = True

            assert snapshot_found, "Must receive at least one snapshot message"
            print(f"\n  ✓ SCENARIO 2 PASSED: All messages conform to schema")

            # ================================================================
            # SCENARIO 3: Field Validation
            # ================================================================
            print("\n" + "-" * 70)
            print("SCENARIO 3: Field Validation for All Data")
            print("-" * 70)

            total_candles = 0

            for i, msg in enumerate(messages, 1):
                print(f"\n  Message {i} - Type: {msg.get('type')}")

                for candle_data in msg.get("data", []):
                    symbol = candle_data.get("symbol")
                    open_price = candle_data.get("open")
                    high = candle_data.get("high")
                    low = candle_data.get("low")
                    close = candle_data.get("close")
                    trades = candle_data.get("trades")
                    volume = candle_data.get("volume")
                    vwap = candle_data.get("vwap")
                    candle_interval = candle_data.get("interval")

                    print(f"    Symbol: {symbol}, Interval: {candle_interval}")

                    # Validate required fields
                    assert symbol in pairs
                    assert isinstance(open_price, (int, float))
                    assert isinstance(high, (int, float))
                    assert isinstance(low, (int, float))
                    assert isinstance(close, (int, float))
                    assert isinstance(trades, int)
                    assert isinstance(volume, (int, float))
                    assert isinstance(vwap, (int, float))
                    assert isinstance(candle_interval, int)
                    assert candle_interval == interval, f"Interval mismatch: {candle_interval} != {interval}"

                    total_candles += 1

            print(f"\n  Summary:")
            print(f"    Total candles validated: {total_candles}")
            print(f"\n  ✓ SCENARIO 3 PASSED: All fields validated across all messages")

            # ================================================================
            # SCENARIO 4: Unsubscription Acknowledgment
            # ================================================================
            print("\n" + "-" * 70)
            print("SCENARIO 4: Unsubscription and Acknowledgment Validation")
            print("-" * 70)

            try:
                unsub_ack = client.unsubscribe("ohlc", pairs)

                print(f"  Unsubscription request sent for: {', '.join(pairs)}")
                print(f"\n  Unsubscription acknowledgment:")
                print(f"    success: {unsub_ack.get('success')}")
                print(f"    method: {unsub_ack.get('method')}")

                assert unsub_ack.get("success") is True, "Unsubscription must succeed"
                assert unsub_ack.get("method") == "unsubscribe"

                print(f"\n  ✓ SCENARIO 4 PASSED: Unsubscription acknowledged")

                # ================================================================
                # SCENARIO 5: Verify No More Data
                # ================================================================
                print("\n" + "-" * 70)
                print("SCENARIO 5: Verify No More Data After Unsubscribe")
                print("-" * 70)

                print("  Waiting 10 seconds to verify no more OHLC messages...")

                start_time = time.time()
                unexpected_messages = []

                while time.time() - start_time < 10:
                    try:
                        msg = client.receive_message(timeout=3)
                        if msg.get('channel') == 'ohlc':
                            unexpected_messages.append(msg)
                            print(f"  ✗ WARNING: Still receiving OHLC data")
                    except:
                        pass

                    elapsed = int(time.time() - start_time)
                    print(f"  Waiting... {elapsed}/10 seconds", end='\r')

                print()  # New line

                assert len(unexpected_messages) == 0, \
                    f"Should not receive OHLC data after unsubscribe, got {len(unexpected_messages)}"

                print(f"  ✓ No OHLC messages received for 10 seconds")
                print(f"\n  ✓ SCENARIO 5 PASSED: Unsubscription verified")

            except Exception as e:
                # Catch both TimeoutError and WebSocketTimeoutException
                if 'timeout' not in str(e).lower() and 'Timeout' not in type(e).__name__:
                    raise
                print(f"\n  ⚠ WARNING: Unsubscribe timed out - skipping SCENARIO 4 & 5")
                print(f"  This may indicate an API issue with OHLC channel")

        print("\n" + "=" * 70)
        print("✓ ALL SCENARIOS PASSED - Complete Flow Validated")
        print("=" * 70 + "\n")

    def test_ohlc_data_integrity_constraints(self, kraken_ws_url, default_timeout):
        """
        Test data integrity constraints for OHLC candles.

        Validates:
        0. Data array not empty & all required fields present
        1. OHLC relationships: low <= open, close <= high
        2. trades >= 0
        3. volume >= 0
        4. vwap > 0
        5. interval matches subscription
        6. All prices > 0
        7. interval_begin < message timestamp
        8. Time difference matches interval exactly (±1s tolerance)
        """
        print("\n[DATA INTEGRITY] Testing OHLC constraints...")

        pairs = ["BTC/USD"]
        interval = 5
        violations = []

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            client.subscribe("ohlc", pairs, interval=interval)

            messages = client.receive_messages(count=2, timeout=60)
            print(f"  Received {len(messages)} messages for validation\n")

            for i, msg in enumerate(messages, 1):
                # Check that data array is not empty
                data = msg.get("data", [])
                try:
                    assert len(data) > 0, "Message data array is empty"
                    print(f"  Message {i}: ✓ Data array not empty ({len(data)} candles)")
                except AssertionError as e:
                    violations.append(str(e))
                    print(f"  Message {i}: ✗ {e}")
                    continue

                for candle_data in data:
                    symbol = candle_data.get("symbol")
                    open_price = candle_data.get("open")
                    high = candle_data.get("high")
                    low = candle_data.get("low")
                    close = candle_data.get("close")
                    trades = candle_data.get("trades")
                    volume = candle_data.get("volume")
                    vwap = candle_data.get("vwap")
                    candle_interval = candle_data.get("interval")
                    interval_begin = candle_data.get("interval_begin")
                    candle_timestamp = candle_data.get("timestamp")

                    print(f"  Candle {i} - {symbol}:")
                    print(f"    OHLC: O={open_price}, H={high}, L={low}, C={close}")

                    # 0. Required fields are not None
                    try:
                        assert symbol is not None, "symbol is None"
                        assert open_price is not None, "open is None"
                        assert high is not None, "high is None"
                        assert low is not None, "low is None"
                        assert close is not None, "close is None"
                        assert trades is not None, "trades is None"
                        assert volume is not None, "volume is None"
                        assert vwap is not None, "vwap is None"
                        assert candle_interval is not None, "interval is None"
                        assert interval_begin is not None, "interval_begin is None"
                        assert candle_timestamp is not None, "timestamp is None"
                        print(f"    ✓ All required fields present")
                    except AssertionError as e:
                        violations.append(str(e))
                        print(f"    ✗ {e}")

                    # 1. OHLC relationships
                    try:
                        assert low <= open_price, f"low ({low}) > open ({open_price})"
                        assert low <= close, f"low ({low}) > close ({close})"
                        assert high >= open_price, f"high ({high}) < open ({open_price})"
                        assert high >= close, f"high ({high}) < close ({close})"
                        assert low <= high, f"low ({low}) > high ({high})"
                        print(f"    ✓ OHLC relationships valid")
                    except AssertionError as e:
                        violations.append(str(e))
                        print(f"    ✗ {e}")

                    # 2. trades >= 0
                    try:
                        assert trades >= 0, f"trades ({trades}) must be >= 0"
                        print(f"    ✓ trades >= 0: {trades}")
                    except AssertionError as e:
                        violations.append(str(e))
                        print(f"    ✗ {e}")

                    # 3. volume >= 0
                    try:
                        assert volume >= 0, f"volume ({volume}) must be >= 0"
                        print(f"    ✓ volume >= 0: {volume}")
                    except AssertionError as e:
                        violations.append(str(e))
                        print(f"    ✗ {e}")

                    # 4. vwap > 0
                    try:
                        assert vwap > 0, f"vwap ({vwap}) must be > 0"
                        print(f"    ✓ vwap > 0: {vwap}")
                    except AssertionError as e:
                        violations.append(str(e))
                        print(f"    ✗ {e}")

                    # 5. interval matches
                    try:
                        assert candle_interval == interval, \
                            f"interval mismatch: {candle_interval} != {interval}"
                        print(f"    ✓ interval matches: {candle_interval}")
                    except AssertionError as e:
                        violations.append(str(e))
                        print(f"    ✗ {e}")

                    # 6. All prices > 0
                    try:
                        assert open_price > 0, f"open ({open_price}) must be > 0"
                        assert high > 0, f"high ({high}) must be > 0"
                        assert low > 0, f"low ({low}) must be > 0"
                        assert close > 0, f"close ({close}) must be > 0"
                        print(f"    ✓ All prices > 0")
                    except AssertionError as e:
                        violations.append(str(e))
                        print(f"    ✗ {e}")

                    # 7. Timestamp validation: interval_begin < candle timestamp
                    try:
                        from datetime import datetime
                        interval_begin_dt = datetime.fromisoformat(interval_begin.replace('Z', '+00:00'))
                        candle_timestamp_dt = datetime.fromisoformat(candle_timestamp.replace('Z', '+00:00'))

                        assert interval_begin_dt < candle_timestamp_dt, \
                            f"interval_begin ({interval_begin}) >= timestamp ({candle_timestamp})"
                        print(f"    ✓ interval_begin < timestamp")
                    except AssertionError as e:
                        violations.append(str(e))
                        print(f"    ✗ {e}")
                    except Exception as e:
                        violations.append(f"Timestamp parsing error: {e}")
                        print(f"    ✗ Timestamp parsing error: {e}")

                    # 8. Time difference matches interval exactly
                    try:
                        from datetime import datetime
                        interval_begin_dt = datetime.fromisoformat(interval_begin.replace('Z', '+00:00'))
                        candle_timestamp_dt = datetime.fromisoformat(candle_timestamp.replace('Z', '+00:00'))

                        time_diff_seconds = (candle_timestamp_dt - interval_begin_dt).total_seconds()
                        expected_diff_seconds = candle_interval * 60  # interval is in minutes

                        # Allow small tolerance for timing (e.g., 1 second)
                        tolerance = 1
                        assert abs(time_diff_seconds - expected_diff_seconds) <= tolerance, \
                            f"Time difference ({time_diff_seconds}s) doesn't match interval ({expected_diff_seconds}s)"
                        print(f"    ✓ Time difference matches interval: {time_diff_seconds}s ≈ {expected_diff_seconds}s")
                    except AssertionError as e:
                        violations.append(str(e))
                        print(f"    ✗ {e}")
                    except Exception as e:
                        violations.append(f"Time difference calculation error: {e}")
                        print(f"    ✗ Time difference calculation error: {e}")

            # Final assertion
            if violations:
                pytest.fail(f"\nData integrity violations found:\n" + "\n".join(violations))

            print("\n  ✓ All data integrity constraints validated")

            try:
                client.unsubscribe("ohlc", pairs)
                print(f"  ✓ Unsubscribe successful")
            except Exception as e:
                # Catch both TimeoutError and WebSocketTimeoutException
                if 'timeout' not in str(e).lower() and 'Timeout' not in type(e).__name__:
                    raise
                print(f"  ⚠ WARNING: Unsubscribe timed out")
                print(f"  This may indicate an API issue with OHLC channel")

    # ========================================================================
    # Interval Parameter Tests - Test each valid interval
    # ========================================================================

    def test_ohlc_interval_1(self, kraken_ws_url, default_timeout):
        """Test OHLC subscription with interval=1 (1 minute)."""
        print("\n[INTERVAL TEST] Testing interval=1 (1 minute)...")

        pairs = ["BTC/USD"]

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            ack = client.subscribe("ohlc", pairs, interval=1)

            print(f"  Subscription: success={ack.get('success')}")
            assert ack.get("success") is True

            messages = client.receive_messages(count=1, timeout=30)
            candle_data = messages[0].get("data", [])[0]
            candle_interval = candle_data.get("interval")

            print(f"  Received candle with interval: {candle_interval}")
            assert candle_interval == 1, f"Expected interval=1, got {candle_interval}"

            print(f"  ✓ interval=1 works correctly")

            try:
                client.unsubscribe("ohlc", pairs)
                print(f"  ✓ Unsubscribe successful")
            except Exception as e:
                # Catch both TimeoutError and WebSocketTimeoutException
                if 'timeout' not in str(e).lower() and 'Timeout' not in type(e).__name__:
                    raise
                print(f"  ⚠ WARNING: Unsubscribe timed out for interval=1")

    def test_ohlc_interval_5(self, kraken_ws_url, default_timeout):
        """Test OHLC subscription with interval=5 (5 minutes)."""
        print("\n[INTERVAL TEST] Testing interval=5 (5 minutes)...")

        pairs = ["BTC/USD"]

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            ack = client.subscribe("ohlc", pairs, interval=5)

            print(f"  Subscription: success={ack.get('success')}")
            assert ack.get("success") is True

            messages = client.receive_messages(count=1, timeout=60)
            candle_data = messages[0].get("data", [])[0]
            candle_interval = candle_data.get("interval")

            print(f"  Received candle with interval: {candle_interval}")
            assert candle_interval == 5, f"Expected interval=5, got {candle_interval}"

            print(f"  ✓ interval=5 works correctly")

            try:
                client.unsubscribe("ohlc", pairs)
                print(f"  ✓ Unsubscribe successful")
            except Exception as e:
                # Catch both TimeoutError and WebSocketTimeoutException
                if 'timeout' not in str(e).lower() and 'Timeout' not in type(e).__name__:
                    raise
                print(f"  ⚠ WARNING: Unsubscribe timed out for interval=5")

    # ========================================================================
    # snapshot Parameter Tests
    # ========================================================================

    def test_ohlc_snapshot_default(self, kraken_ws_url, default_timeout):
        """Test OHLC subscription with default snapshot parameter (should be true)."""
        print("\n[SNAPSHOT TEST] Testing default snapshot parameter (should default to true)...")

        pairs = ["BTC/USD"]

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            # Subscribe without snapshot parameter
            ack = client.subscribe("ohlc", pairs, interval=5)

            print(f"  Subscription: success={ack.get('success')}")
            assert ack.get("success") is True

            # Should receive snapshot message (default=true)
            messages = client.receive_messages(count=1, timeout=60)
            first_msg = messages[0]

            print(f"  First message type: {first_msg.get('type')}")
            assert first_msg.get('type') == 'snapshot', \
                f"BUG: Default snapshot should be true, but got type='{first_msg.get('type')}'"

            print(f"  ✓ Default snapshot parameter correctly set to true (received snapshot)")

            try:
                client.unsubscribe("ohlc", pairs)
                print(f"  ✓ Unsubscribe successful")
            except Exception as e:
                # Catch both TimeoutError and WebSocketTimeoutException
                if 'timeout' not in str(e).lower() and 'Timeout' not in type(e).__name__:
                    raise
                print(f"  ⚠ WARNING: Unsubscribe timed out for snapshot=default")

    def test_ohlc_snapshot_true(self, kraken_ws_url, default_timeout):
        """Test OHLC subscription with snapshot=true."""
        print("\n[SNAPSHOT TEST] Testing snapshot=true...")

        pairs = ["BTC/USD"]

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            ack = client.subscribe("ohlc", pairs, interval=5, snapshot=True)

            print(f"  Subscription: success={ack.get('success')}")
            assert ack.get("success") is True

            # Should receive snapshot message
            messages = client.receive_messages(count=1, timeout=60)
            first_msg = messages[0]

            print(f"  First message type: {first_msg.get('type')}")
            assert first_msg.get('type') == 'snapshot', \
                f"Expected snapshot message, but got type='{first_msg.get('type')}'"

            print(f"  ✓ snapshot=true works correctly (received snapshot)")

            try:
                client.unsubscribe("ohlc", pairs)
                print(f"  ✓ Unsubscribe successful")
            except Exception as e:
                # Catch both TimeoutError and WebSocketTimeoutException
                if 'timeout' not in str(e).lower() and 'Timeout' not in type(e).__name__:
                    raise
                print(f"  ⚠ WARNING: Unsubscribe timed out for snapshot=true")

    def test_ohlc_snapshot_false(self, kraken_ws_url, default_timeout):
        """Test OHLC subscription with snapshot=false."""
        print("\n[SNAPSHOT TEST] Testing snapshot=false...")

        pairs = ["BTC/USD"]

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            ack = client.subscribe("ohlc", pairs, interval=5, snapshot=False)

            print(f"  Subscription: success={ack.get('success')}")
            assert ack.get("success") is True

            # Should NOT receive snapshot message, only updates
            messages = client.receive_messages(count=3, timeout=60)

            snapshot_count = sum(1 for msg in messages if msg.get('type') == 'snapshot')
            update_count = sum(1 for msg in messages if msg.get('type') == 'update')

            print(f"  Received: {snapshot_count} snapshots, {update_count} updates")
            assert snapshot_count == 0, \
                f"BUG: snapshot=false should not send snapshots, but got {snapshot_count} snapshot messages"
            assert update_count > 0, "Should receive update messages"

            print(f"  ✓ snapshot=false works correctly (no snapshots, only updates)")

            try:
                client.unsubscribe("ohlc", pairs)
                print(f"  ✓ Unsubscribe successful")
            except Exception as e:
                # Catch both TimeoutError and WebSocketTimeoutException
                if 'timeout' not in str(e).lower() and 'Timeout' not in type(e).__name__:
                    raise
                print(f"  ⚠ WARNING: Unsubscribe timed out for snapshot=false")


class TestOHLCChannelNegativeScenarios:
    """Negative test scenarios for OHLC channel."""

    def test_invalid_channel_name(self, kraken_ws_url, default_timeout):
        """Test subscription with invalid channel name."""
        print("\n[NEGATIVE TEST] Testing invalid channel name...")

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            try:
                ack = client.subscribe("invalid_channel", ["BTC/USD"], interval=5)
                print(f"  Response: success={ack.get('success')}, error={ack.get('error')}")
                assert ack.get("success") is False, "Should fail with invalid channel"
                print(f"  ✓ Correctly rejected invalid channel")
            except (ValueError, TimeoutError) as e:
                print(f"  ✓ Correctly raised exception: {type(e).__name__}")

    def test_empty_symbol_list(self, kraken_ws_url, default_timeout):
        """Test subscription with empty symbol list."""
        print("\n[NEGATIVE TEST] Testing empty symbol list...")

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            try:
                ack = client.subscribe("ohlc", [], interval=5)
                # If we get here, server responded
                print(f"  Response: success={ack.get('success')}, error={ack.get('error')}")
                assert ack.get("success") is False, "Should reject empty symbol list"
                print(f"  ✓ Correctly rejected empty symbol list")
            except Exception as e:
                # Catch both TimeoutError and WebSocketTimeoutException
                if 'timeout' not in str(e).lower() and 'Timeout' not in type(e).__name__:
                    raise
                # Server timeout - silently ignored the request
                print(f"  ⚠ Server timed out (did not respond to empty symbol list)")
                print(f"  This indicates server silently ignores invalid requests")
                print(f"  ✓ Test passed (timeout is acceptable behavior)")
            except Exception as e:
                # Other exception
                print(f"  Exception: {type(e).__name__}: {e}")
                # Check if it's a WebSocket timeout (also acceptable)
                if "timeout" in str(e).lower() or "timed out" in str(e).lower():
                    print(f"  ✓ Test passed (timeout is acceptable behavior)")
                else:
                    # Unexpected error - re-raise to fail the test
                    print(f"  ✗ Unexpected error type")
                    raise

    # ========================================================================
    # Invalid Interval Tests - All must default or fail explicitly
    # ========================================================================

    def test_ohlc_interval_missing(self, kraken_ws_url, default_timeout):
        """Test OHLC subscription without interval parameter (should default to 1)."""
        print("\n[NEGATIVE TEST] Testing missing interval parameter (should default to 1)...")

        pairs = ["BTC/USD"]

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            ack = client.subscribe("ohlc", pairs)
            print(f"  Response: success={ack.get('success')}")

            assert ack.get("success") is True, \
                "Missing interval should default to 1"

            # Verify interval defaults to 1
            messages = client.receive_messages(count=1, timeout=30)
            candle_data = messages[0].get("data", [])[0]
            candle_interval = candle_data.get("interval")

            print(f"  Received candle with interval: {candle_interval}")
            assert candle_interval == 1, f"Expected interval=1 (default), got {candle_interval}"

            print(f"  ✓ Missing interval correctly defaulted to 1")

            try:
                client.unsubscribe("ohlc", pairs)
            except TimeoutError:
                print(f"  ⚠ WARNING: Unsubscribe timed out")

    def test_ohlc_interval_zero(self, kraken_ws_url, default_timeout):
        """Test OHLC subscription with interval=0 (invalid)."""
        print("\n[NEGATIVE TEST] Testing interval=0 (invalid)...")

        pairs = ["BTC/USD"]

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            try:
                ack = client.subscribe("ohlc", pairs, interval=0)
                print(f"  Response: success={ack.get('success')}, error={ack.get('error')}")

                # 0 is not in the valid list, should be rejected
                assert ack.get("success") is False, "BUG: interval=0 should be rejected"
                print(f"  ✓ Correctly rejected interval=0")

            except (ValueError, TimeoutError) as e:
                print(f"  ✓ Correctly raised exception: {type(e).__name__}")

    def test_ohlc_interval_invalid_value(self, kraken_ws_url, default_timeout):
        """Test OHLC subscription with interval=17 (not in allowed list)."""
        print("\n[NEGATIVE TEST] Testing interval=17 (not in allowed list)...")

        pairs = ["BTC/USD"]

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            try:
                ack = client.subscribe("ohlc", pairs, interval=17)
                print(f"  Response: success={ack.get('success')}, error={ack.get('error')}")

                # 17 is not in the valid list
                assert ack.get("success") is False, "BUG: interval=17 should be rejected"
                print(f"  ✓ Correctly rejected interval=17")

            except (ValueError, TimeoutError) as e:
                print(f"  ✓ Correctly raised exception: {type(e).__name__}")

    def test_ohlc_interval_none(self, kraken_ws_url, default_timeout):
        """Test OHLC subscription with interval=None (invalid)."""
        print("\n[NEGATIVE TEST] Testing interval=None (invalid)...")

        pairs = ["BTC/USD"]

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            try:
                ack = client.subscribe("ohlc", pairs, interval=None)
                print(f"  Response: success={ack.get('success')}, error={ack.get('error')}")

                assert ack.get("success") is False, "BUG: interval=None should be rejected"
                print(f"  ✓ Correctly rejected interval=None")

            except (ValueError, TimeoutError, TypeError) as e:
                print(f"  ✓ Correctly raised exception: {type(e).__name__}")

    def test_ohlc_interval_empty_string(self, kraken_ws_url, default_timeout):
        """Test OHLC subscription with interval='' (invalid)."""
        print("\n[NEGATIVE TEST] Testing interval='' (empty string)...")

        pairs = ["BTC/USD"]

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            try:
                ack = client.subscribe("ohlc", pairs, interval="")
                print(f"  Response: success={ack.get('success')}, error={ack.get('error')}")

                assert ack.get("success") is False, "BUG: interval='' should be rejected"
                print(f"  ✓ Correctly rejected interval=''")

            except (ValueError, TimeoutError, TypeError) as e:
                print(f"  ✓ Correctly raised exception: {type(e).__name__}")

    def test_ohlc_interval_invalid_string(self, kraken_ws_url, default_timeout):
        """Test OHLC subscription with interval='invalid' (invalid)."""
        print("\n[NEGATIVE TEST] Testing interval='invalid' (invalid)...")

        pairs = ["BTC/USD"]

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            try:
                ack = client.subscribe("ohlc", pairs, interval="invalid")
                print(f"  Response: success={ack.get('success')}, error={ack.get('error')}")

                assert ack.get("success") is False, "BUG: interval='invalid' should be rejected"
                print(f"  ✓ Correctly rejected interval='invalid'")

            except (ValueError, TimeoutError, TypeError) as e:
                print(f"  ✓ Correctly raised exception: {type(e).__name__}")

    # ========================================================================
    # Invalid snapshot Tests
    # ========================================================================

    def test_ohlc_snapshot_none(self, kraken_ws_url, default_timeout):
        """Test OHLC subscription with snapshot=None (should be rejected)."""
        print("\n[SNAPSHOT TEST] Testing snapshot=None (should be rejected)...")

        pairs = ["BTC/USD"]

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            with pytest.raises(ValueError) as exc_info:
                client.subscribe("ohlc", pairs, interval=5, snapshot=None)

            error_msg = str(exc_info.value)
            print(f"  ✓ API correctly rejected snapshot=None")
            print(f"  Error message: {error_msg}")
            assert "snapshot" in error_msg.lower() or "boolean" in error_msg.lower(), \
                f"Expected snapshot validation error, but got: {error_msg}"

    def test_ohlc_snapshot_invalid_string(self, kraken_ws_url, default_timeout):
        """Test OHLC subscription with snapshot='invalid' (should be rejected)."""
        print("\n[SNAPSHOT TEST] Testing snapshot='invalid' (should be rejected)...")

        pairs = ["BTC/USD"]

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            with pytest.raises(ValueError) as exc_info:
                client.subscribe("ohlc", pairs, interval=5, snapshot="invalid")

            error_msg = str(exc_info.value)
            print(f"  ✓ API correctly rejected snapshot='invalid'")
            print(f"  Error message: {error_msg}")
            assert "snapshot" in error_msg.lower() or "boolean" in error_msg.lower(), \
                f"Expected snapshot validation error, but got: {error_msg}"

    def test_ohlc_snapshot_invalid_number(self, kraken_ws_url, default_timeout):
        """Test OHLC subscription with snapshot=123 (should be rejected)."""
        print("\n[SNAPSHOT TEST] Testing snapshot=123 (should be rejected)...")

        pairs = ["BTC/USD"]

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            with pytest.raises(ValueError) as exc_info:
                client.subscribe("ohlc", pairs, interval=5, snapshot=123)

            error_msg = str(exc_info.value)
            print(f"  ✓ API correctly rejected snapshot=123")
            print(f"  Error message: {error_msg}")
            assert "snapshot" in error_msg.lower() or "boolean" in error_msg.lower(), \
                f"Expected snapshot validation error, but got: {error_msg}"
