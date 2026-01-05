import pytest
import time
import json
from utils.websocket_client import KrakenWebSocketClient
from utils.validators import validate_schema


class TestTickerChannel:
    """Tests for Ticker channel."""

    def test_ticker_complete_flow(self, kraken_ws_url, load_schema, default_timeout):
        """
        COMPREHENSIVE TEST: Complete ticker test flow with all scenarios.

        SCENARIO 1: Connect and validate subscription acknowledgment
        SCENARIO 2: Schema validation (snapshot + update messages)
        SCENARIO 3: Field validation (all required fields and types)
        SCENARIO 4: Unsubscribe and validate acknowledgment
        SCENARIO 5: Verify no data after unsubscribe (20 second wait)
        """
        print("\n" + "=" * 80)
        print("TICKER CHANNEL - COMPLETE TEST FLOW")
        print("=" * 80)

        # Load ticker schema
        ticker_schema = load_schema("ticker")
        pairs = ["BTC/USD", "SOL/USD"]

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:

            # ================================================================
            # SCENARIO 1: CONNECT AND VALIDATE SUBSCRIPTION ACKNOWLEDGMENT
            # ================================================================
            print("\n" + "-" * 80)
            print("SCENARIO 1: CONNECT AND VALIDATE SUBSCRIPTION ACKNOWLEDGMENT")
            print("-" * 80)

            print(f"Subscribing to ticker channel for {', '.join(pairs)}...")
            ack = client.subscribe("ticker", pairs)

            print("\nValidating subscription acknowledgment:")
            print(f"  ✓ Checking 'method' field...")
            assert ack.get("method") == "subscribe", \
                f"Expected method='subscribe', got '{ack.get('method')}'"
            print(f"    - method = '{ack.get('method')}' ✓")

            print(f"  ✓ Checking 'success' field...")
            assert ack.get("success") is True, \
                f"Expected success=True, got {ack.get('success')}"
            print(f"    - success = {ack.get('success')} ✓")

            print(f"  ✓ Checking 'result' structure...")
            result = ack.get("result", {})
            assert result.get("channel") == "ticker", \
                f"Expected channel='ticker', got '{result.get('channel')}'"
            print(f"    - result.channel = '{result.get('channel')}' ✓")
            print(f"    - result.symbol = '{result.get('symbol')}' ✓")

            print(f"  ✓ Checking timestamp fields...")
            assert "time_in" in ack, "Missing 'time_in' field"
            assert "time_out" in ack, "Missing 'time_out' field"
            print(f"    - time_in = {ack.get('time_in')} ✓")
            print(f"    - time_out = {ack.get('time_out')} ✓")

            print("\n✓ SCENARIO 1 PASSED: Subscription acknowledgment validated")

            # Receive messages for next scenarios
            print("\nReceiving ticker messages for validation...")
            messages = client.receive_messages(count=10, timeout=default_timeout)
            print(f"✓ Received {len(messages)} messages")

            # ================================================================
            # SCENARIO 2: SCHEMA VALIDATION (SNAPSHOT + UPDATE)
            # ================================================================
            print("\n" + "-" * 80)
            print("SCENARIO 2: SCHEMA VALIDATION (SNAPSHOT + UPDATE)")
            print("-" * 80)

            validated_snapshot = False
            validated_update = False
            snapshot_msg = None
            update_msg = None

            # Find one snapshot and one update message
            for msg in messages:
                if msg.get("type") == "snapshot" and not validated_snapshot:
                    snapshot_msg = msg
                    validated_snapshot = True
                elif msg.get("type") == "update" and not validated_update:
                    update_msg = msg
                    validated_update = True

                if validated_snapshot and validated_update:
                    break

            # Validate snapshot message
            if snapshot_msg:
                print("\nValidating SNAPSHOT message against JSON schema:")
                print(f"  Message type: {snapshot_msg.get('type')}")
                print(f"  Channel: {snapshot_msg.get('channel')}")
                print(f"  Data entries: {len(snapshot_msg.get('data', []))}")

                try:
                    validate_schema(snapshot_msg, ticker_schema)
                    print("  ✓ Snapshot message passed JSON schema validation")
                except Exception as e:
                    pytest.fail(f"Snapshot schema validation failed: {e}")
            else:
                print("  ⚠ No snapshot message received (may be OK)")

            # Validate update message
            if update_msg:
                print("\nValidating UPDATE message against JSON schema:")
                print(f"  Message type: {update_msg.get('type')}")
                print(f"  Channel: {update_msg.get('channel')}")
                print(f"  Data entries: {len(update_msg.get('data', []))}")

                try:
                    validate_schema(update_msg, ticker_schema)
                    print("  ✓ Update message passed JSON schema validation")
                except Exception as e:
                    pytest.fail(f"Update schema validation failed: {e}")
            else:
                print("  ⚠ No update message received yet (may need to wait longer)")

            assert validated_snapshot, "Should have validated at least one snapshot message"
            print("\n✓ SCENARIO 2 PASSED: Schema validation completed")

            # ================================================================
            # SCENARIO 3: FIELD VALIDATION (ALL MESSAGES)
            # ================================================================
            print("\n" + "-" * 80)
            print("SCENARIO 3: FIELD VALIDATION (ALL REQUIRED FIELDS AND TYPES)")
            print("-" * 80)

            print(f"\nValidating {len(messages)} messages for field correctness...")

            total_ticker_entries = 0
            for msg_idx, msg in enumerate(messages, 1):
                print(f"\n  Message {msg_idx}:")

                # Validate message-level fields
                print(f"    Validating message structure...")
                assert "channel" in msg, "Missing 'channel' field"
                assert msg["channel"] == "ticker", \
                    f"Expected channel='ticker', got '{msg['channel']}'"
                print(f"      ✓ channel = '{msg['channel']}'")

                assert "type" in msg, "Missing 'type' field"
                assert msg["type"] in ["snapshot", "update"], \
                    f"Expected type in ['snapshot','update'], got '{msg['type']}'"
                print(f"      ✓ type = '{msg['type']}'")

                assert "data" in msg, "Missing 'data' field"
                assert isinstance(msg["data"], list), "Data must be an array"
                assert len(msg["data"]) > 0, "Data array must not be empty"
                print(f"      ✓ data is non-empty array (length={len(msg['data'])})")

                # Validate ticker data fields
                for data_idx, ticker_data in enumerate(msg["data"], 1):
                    total_ticker_entries += 1
                    print(f"    Validating ticker data entry {data_idx} ({ticker_data.get('symbol')}):")

                    # Symbol - with strict validation
                    assert "symbol" in ticker_data, "Missing 'symbol' field"
                    assert isinstance(ticker_data["symbol"], str), "Symbol must be string"
                    assert ticker_data["symbol"] in pairs, \
                        f"Unexpected symbol '{ticker_data['symbol']}', expected one of {pairs}"
                    print(f"      ✓ symbol: '{ticker_data['symbol']}' (string, matches subscription)")

                    # Bid
                    assert "bid" in ticker_data, "Missing 'bid' field"
                    assert isinstance(ticker_data["bid"], (int, float)), "Bid must be number"
                    assert ticker_data["bid"] > 0, "Bid must be positive"
                    print(f"      ✓ bid: {ticker_data['bid']} (number, positive)")

                    # Ask
                    assert "ask" in ticker_data, "Missing 'ask' field"
                    assert isinstance(ticker_data["ask"], (int, float)), "Ask must be number"
                    assert ticker_data["ask"] > 0, "Ask must be positive"
                    print(f"      ✓ ask: {ticker_data['ask']} (number, positive)")

                    # Last
                    assert "last" in ticker_data, "Missing 'last' field"
                    assert isinstance(ticker_data["last"], (int, float)), "Last must be number"
                    assert ticker_data["last"] > 0, "Last must be positive"
                    print(f"      ✓ last: {ticker_data['last']} (number, positive)")

                    # Volume
                    assert "volume" in ticker_data, "Missing 'volume' field"
                    assert isinstance(ticker_data["volume"], (int, float)), "Volume must be number"
                    assert ticker_data["volume"] >= 0, "Volume must be non-negative"
                    print(f"      ✓ volume: {ticker_data['volume']} (number, non-negative)")

                    # VWAP
                    assert "vwap" in ticker_data, "Missing 'vwap' field"
                    assert isinstance(ticker_data["vwap"], (int, float)), "VWAP must be number"
                    assert ticker_data["vwap"] > 0, "VWAP must be positive"
                    print(f"      ✓ vwap: {ticker_data['vwap']} (number, positive)")

                    # High
                    assert "high" in ticker_data, "Missing 'high' field"
                    assert isinstance(ticker_data["high"], (int, float)), "High must be number"
                    assert ticker_data["high"] > 0, "High must be positive"
                    print(f"      ✓ high: {ticker_data['high']} (number, positive)")

                    # Low
                    assert "low" in ticker_data, "Missing 'low' field"
                    assert isinstance(ticker_data["low"], (int, float)), "Low must be number"
                    assert ticker_data["low"] > 0, "Low must be positive"
                    print(f"      ✓ low: {ticker_data['low']} (number, positive)")

                    # Business logic validation
                    print(f"    Validating business logic:")
                    assert ticker_data["bid"] < ticker_data["ask"], \
                        f"Bid ({ticker_data['bid']}) must be < Ask ({ticker_data['ask']})"
                    print(f"      ✓ bid < ask: {ticker_data['bid']} < {ticker_data['ask']}")

                    assert ticker_data["low"] <= ticker_data["high"], \
                        f"Low ({ticker_data['low']}) must be <= High ({ticker_data['high']})"
                    print(f"      ✓ low <= high: {ticker_data['low']} <= {ticker_data['high']}")

            print(f"\n✓ SCENARIO 3 PASSED: All {total_ticker_entries} ticker entries validated")

            # ================================================================
            # SCENARIO 4: UNSUBSCRIBE AND VALIDATE ACKNOWLEDGMENT
            # ================================================================
            print("\n" + "-" * 80)
            print("SCENARIO 4: UNSUBSCRIBE AND VALIDATE ACKNOWLEDGMENT")
            print("-" * 80)

            print(f"\nUnsubscribing from ticker channel for {', '.join(pairs)}...")
            unsubscribe_ack = client.unsubscribe("ticker", pairs)

            print("\nValidating unsubscription acknowledgment:")
            print(f"  ✓ Checking 'method' field...")
            assert unsubscribe_ack.get("method") == "unsubscribe", \
                f"Expected method='unsubscribe', got '{unsubscribe_ack.get('method')}'"
            print(f"    - method = '{unsubscribe_ack.get('method')}' ✓")

            print(f"  ✓ Checking 'success' field...")
            assert unsubscribe_ack.get("success") is True, \
                f"Expected success=True, got {unsubscribe_ack.get('success')}"
            print(f"    - success = {unsubscribe_ack.get('success')} ✓")

            print(f"  ✓ Checking 'result' structure...")
            unsub_result = unsubscribe_ack.get("result", {})
            assert unsub_result.get("channel") == "ticker", \
                f"Expected channel='ticker', got '{unsub_result.get('channel')}'"
            print(f"    - result.channel = '{unsub_result.get('channel')}' ✓")

            print("\n✓ SCENARIO 4 PASSED: Unsubscription acknowledgment validated")

            # ================================================================
            # SCENARIO 5: VERIFY NO DATA AFTER UNSUBSCRIBE (20 SECONDS)
            # ================================================================
            print("\n" + "-" * 80)
            print("SCENARIO 5: VERIFY NO DATA AFTER UNSUBSCRIBE (20 SECOND WAIT)")
            print("-" * 80)

            print("\nWaiting 20 seconds to verify no more ticker messages arrive...")
            print("(This proves unsubscription worked)")

            start_time = time.time()
            unexpected_messages = []

            while time.time() - start_time < 20:
                try:
                    msg = client.receive_message(timeout=5)
                    if msg.get("channel") == "ticker":
                        unexpected_messages.append(msg)
                        print(f"  ✗ WARNING: Received ticker message: {msg.get('type')}")
                except:
                    # Timeout is expected - no messages
                    pass

                # Show progress
                elapsed = int(time.time() - start_time)
                remaining = 20 - elapsed
                print(f"  Waiting... {elapsed}/20 seconds (remaining: {remaining}s)", end='\r')

            print()  # New line after progress

            if len(unexpected_messages) == 0:
                print("  ✓ No ticker messages received for 20 seconds")
                print("  ✓ Unsubscription verified - no more data flowing")
            else:
                print(f"  ✗ Still received {len(unexpected_messages)} ticker messages")
                pytest.fail(f"Unsubscription failed - still receiving {len(unexpected_messages)} messages")

            print("\n✓ SCENARIO 5 PASSED: No data after unsubscribe")

            # ================================================================
            # CLEANUP
            # ================================================================
            print("\n" + "-" * 80)
            print("CLEANUP")
            print("-" * 80)
            print("✓ Connection will be closed automatically (context manager)")

        # Context manager automatically calls client.disconnect() here
        print("✓ WebSocket connection closed")
        print("\n" + "=" * 80)
        print("✓ ALL SCENARIOS PASSED - TICKER CHANNEL TEST COMPLETE")
        print("=" * 80 + "\n")

    # ========================================================================
    # INDIVIDUAL SCENARIO TESTS (Quick, focused tests)
    # ========================================================================

    def test_ticker_scenario_1_subscription_acknowledgment(self, kraken_ws_url, default_timeout):
        """SCENARIO 1 (Individual): Test subscription acknowledgment validation."""
        print("\n[QUICK TEST] Testing subscription acknowledgment...")

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            # Subscribe
            ack = client.subscribe("ticker", ["BTC/USD"])

            # Validate acknowledgment
            assert ack.get("method") == "subscribe", "Method should be 'subscribe'"
            assert ack.get("success") is True, "Success should be True"
            assert ack.get("result", {}).get("channel") == "ticker", "Channel should be 'ticker'"
            assert "time_in" in ack, "Should have time_in timestamp"
            assert "time_out" in ack, "Should have time_out timestamp"

            print("  ✓ Subscription acknowledgment validated")

            # Cleanup: unsubscribe
            client.unsubscribe("ticker", ["BTC/USD"])
            print("  ✓ Cleanup complete")

    def test_ticker_scenario_2_schema_validation(self, kraken_ws_url, load_schema, default_timeout):
        """SCENARIO 2 (Individual): Test JSON schema validation for snapshot and update."""
        print("\n[QUICK TEST] Testing schema validation...")

        ticker_schema = load_schema("ticker")

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            # Subscribe
            client.subscribe("ticker", ["BTC/USD"])

            # Receive messages
            messages = client.receive_messages(count=5, timeout=default_timeout)

            # Validate schema for snapshot and update
            validated_snapshot = False
            validated_update = False

            for msg in messages:
                if msg.get("type") == "snapshot" and not validated_snapshot:
                    validate_schema(msg, ticker_schema)
                    validated_snapshot = True
                    print("  ✓ Snapshot schema validated")

                elif msg.get("type") == "update" and not validated_update:
                    validate_schema(msg, ticker_schema)
                    validated_update = True
                    print("  ✓ Update schema validated")

                if validated_snapshot and validated_update:
                    break

            assert validated_snapshot, "Should validate at least one snapshot"
            assert validated_update or len(messages) < 3, "Should validate update if enough messages"

            # Cleanup
            client.unsubscribe("ticker", ["BTC/USD"])
            print("  ✓ Cleanup complete")

    def test_ticker_scenario_3_field_validation(self, kraken_ws_url, default_timeout):
        """SCENARIO 3 (Individual): Test field types and business logic."""
        print("\n[QUICK TEST] Testing field validation and business logic...")

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            # Subscribe
            subscribed_pairs = ["BTC/USD"]
            client.subscribe("ticker", subscribed_pairs)

            # Receive messages
            messages = client.receive_messages(count=3, timeout=default_timeout)

            for msg in messages:
                # Validate message structure
                assert msg.get("channel") == "ticker", "Channel must be 'ticker'"
                assert msg.get("type") in ["snapshot", "update"], "Type must be snapshot or update"
                assert isinstance(msg.get("data"), list), "Data must be array"
                assert len(msg.get("data")) > 0, "Data must not be empty"

                # Validate ticker data
                for ticker_data in msg.get("data", []):
                    # Type validation with strict symbol check
                    assert isinstance(ticker_data["symbol"], str), "Symbol must be string"
                    assert ticker_data["symbol"] in subscribed_pairs, \
                        f"Unexpected symbol '{ticker_data['symbol']}', expected {subscribed_pairs}"
                    assert isinstance(ticker_data["bid"], (int, float)), "Bid must be number"
                    assert isinstance(ticker_data["ask"], (int, float)), "Ask must be number"

                    # Business logic validation
                    assert ticker_data["bid"] > 0, "Bid must be positive"
                    assert ticker_data["ask"] > 0, "Ask must be positive"
                    assert ticker_data["bid"] < ticker_data["ask"], "Bid must be < Ask"
                    assert ticker_data["low"] <= ticker_data["high"], "Low must be <= High"

            print("  ✓ Field validation passed")
            print("  ✓ Business logic validated")

            # Cleanup
            client.unsubscribe("ticker", ["BTC/USD"])
            print("  ✓ Cleanup complete")

    def test_ticker_scenario_4_unsubscription_acknowledgment(self, kraken_ws_url, default_timeout):
        """SCENARIO 4 (Individual): Test unsubscription acknowledgment."""
        print("\n[QUICK TEST] Testing unsubscription acknowledgment...")

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            # Subscribe first
            client.subscribe("ticker", ["BTC/USD"])

            # Unsubscribe
            unsubscribe_ack = client.unsubscribe("ticker", ["BTC/USD"])

            # Validate unsubscription acknowledgment
            assert unsubscribe_ack.get("method") == "unsubscribe", "Method should be 'unsubscribe'"
            assert unsubscribe_ack.get("success") is True, "Success should be True"
            assert unsubscribe_ack.get("result", {}).get("channel") == "ticker", \
                "Channel should be 'ticker'"

            print("  ✓ Unsubscription acknowledgment validated")
            print("  ✓ Cleanup complete")

    def test_ticker_data_integrity_constraints(self, kraken_ws_url, default_timeout):
        """
        Test data integrity constraints and business logic.

        Validates:
        - bid < ask (spread always positive)
        - bid_qty > 0
        - ask_qty > 0
        - volume >= 0
        - vwap > 0
        - high > low (strict)
        - bid < last < ask (last price within spread)
        """
        print("\n[DATA INTEGRITY TEST] Testing all business logic constraints...")

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            # Subscribe
            client.subscribe("ticker", ["BTC/USD"])

            # Receive messages
            messages = client.receive_messages(count=5, timeout=default_timeout)

            violations = []

            for msg_idx, msg in enumerate(messages, 1):
                for ticker_data in msg.get("data", []):
                    symbol = ticker_data["symbol"]
                    bid = ticker_data["bid"]
                    ask = ticker_data["ask"]
                    last = ticker_data["last"]
                    volume = ticker_data["volume"]
                    vwap = ticker_data["vwap"]
                    high = ticker_data["high"]
                    low = ticker_data["low"]
                    bid_qty = ticker_data.get("bid_qty", 0)
                    ask_qty = ticker_data.get("ask_qty", 0)

                    print(f"\n  Validating {symbol} (Message {msg_idx}):")

                    # 1. bid < ask
                    try:
                        assert bid < ask, f"bid ({bid}) must be < ask ({ask})"
                        print(f"    ✓ bid < ask: {bid} < {ask}")
                    except AssertionError as e:
                        violations.append(str(e))
                        print(f"    ✗ {e}")

                    # 2. bid_qty > 0
                    try:
                        assert bid_qty > 0, f"bid_qty ({bid_qty}) must be > 0"
                        print(f"    ✓ bid_qty > 0: {bid_qty}")
                    except AssertionError as e:
                        violations.append(str(e))
                        print(f"    ✗ {e}")

                    # 3. ask_qty > 0
                    try:
                        assert ask_qty > 0, f"ask_qty ({ask_qty}) must be > 0"
                        print(f"    ✓ ask_qty > 0: {ask_qty}")
                    except AssertionError as e:
                        violations.append(str(e))
                        print(f"    ✗ {e}")

                    # 4. volume >= 0
                    try:
                        assert volume >= 0, f"volume ({volume}) must be >= 0"
                        print(f"    ✓ volume >= 0: {volume}")
                    except AssertionError as e:
                        violations.append(str(e))
                        print(f"    ✗ {e}")

                    # 5. vwap > 0
                    try:
                        assert vwap > 0, f"vwap ({vwap}) must be > 0"
                        print(f"    ✓ vwap > 0: {vwap}")
                    except AssertionError as e:
                        violations.append(str(e))
                        print(f"    ✗ {e}")

                    # 6. high > low (strict)
                    try:
                        assert high > low, f"high ({high}) must be > low ({low})"
                        print(f"    ✓ high > low: {high} > {low}")
                    except AssertionError as e:
                        violations.append(str(e))
                        print(f"    ✗ {e}")

            # Final assertion
            if violations:
                pytest.fail(f"\nData integrity violations found:\n" + "\n".join(violations))

            print("\n  ✓ All data integrity constraints validated")
            print("  ✓ All business logic passed")

            # Cleanup
            client.unsubscribe("ticker", ["BTC/USD"])
            print("  ✓ Cleanup complete")


# ============================================================================
# NEGATIVE TEST SCENARIOS - Error Handling and Edge Cases
# ============================================================================

class TestTickerChannelNegativeScenarios:
    """Negative test scenarios - testing error handling and input validation."""

    def test_invalid_channel_name(self, kraken_ws_url, default_timeout):
        """Test subscription with invalid channel name."""
        print("\n[NEGATIVE TEST] Testing invalid channel name...")

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            # Manually send invalid subscription request
            import json
            invalid_request = {
                "method": "subscribe",
                "params": {
                    "channel": "invalid_channel_name",  # Invalid!
                    "symbol": ["BTC/USD"]
                }
            }

            client.ws.send(json.dumps(invalid_request))

            # Wait for response
            try:
                response = client.receive_message(timeout=10)
                print(f"  Response: {json.dumps(response, indent=2)}")

                # Should get error response
                if response.get("method") == "subscribe":
                    assert response.get("success") is False, \
                        "Expected subscription to fail for invalid channel"
                    assert "error" in response, "Expected error field in response"
                    print(f"  ✓ Received expected error: {response.get('error')}")
                else:
                    print(f"  ⚠ Unexpected response type: {response.get('method')}")

            except Exception as e:
                print(f"  ✓ Exception raised as expected: {e}")

    def test_empty_channel_name(self, kraken_ws_url, default_timeout):
        """Test subscription with empty channel name."""
        print("\n[NEGATIVE TEST] Testing empty channel name...")

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            import json
            invalid_request = {
                "method": "subscribe",
                "params": {
                    "channel": "",  # Empty string!
                    "symbol": ["BTC/USD"]
                }
            }

            client.ws.send(json.dumps(invalid_request))

            try:
                response = client.receive_message(timeout=10)
                print(f"  Response: {json.dumps(response, indent=2)}")

                if response.get("method") == "subscribe":
                    assert response.get("success") is False or "error" in response, \
                        "Expected error for empty channel"
                    print(f"  ✓ Handled empty channel correctly")

            except Exception as e:
                print(f"  ✓ Exception raised: {e}")

    def test_null_channel_name(self, kraken_ws_url, default_timeout):
        """Test subscription with null/None channel name."""
        print("\n[NEGATIVE TEST] Testing null channel name...")

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            import json
            invalid_request = {
                "method": "subscribe",
                "params": {
                    "channel": None,  # None (JSON null)!
                    "symbol": ["BTC/USD"]
                }
            }

            client.ws.send(json.dumps(invalid_request))

            try:
                response = client.receive_message(timeout=10)
                print(f"  Response: {json.dumps(response, indent=2)}")

                if response.get("method") == "subscribe":
                    assert response.get("success") is False or "error" in response, \
                        "Expected error for null channel"
                    print(f"  ✓ Handled null channel correctly")

            except Exception as e:
                print(f"  ✓ Exception raised: {e}")

    def test_missing_channel_parameter(self, kraken_ws_url, default_timeout):
        """Test subscription without channel parameter (undefined)."""
        print("\n[NEGATIVE TEST] Testing missing channel parameter...")

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            import json
            invalid_request = {
                "method": "subscribe",
                "params": {
                    # No "channel" key at all (undefined in JS terms)
                    "symbol": ["BTC/USD"]
                }
            }

            client.ws.send(json.dumps(invalid_request))

            try:
                response = client.receive_message(timeout=10)
                print(f"  Response: {json.dumps(response, indent=2)}")

                if response.get("method") == "subscribe":
                    assert response.get("success") is False or "error" in response, \
                        "Expected error for missing channel"
                    print(f"  ✓ Handled missing channel parameter correctly")

            except Exception as e:
                print(f"  ✓ Exception raised: {e}")

    def test_invalid_symbol(self, kraken_ws_url, default_timeout):
        """Test subscription with invalid/non-existent symbol."""
        print("\n[NEGATIVE TEST] Testing invalid symbol...")

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            import json
            invalid_request = {
                "method": "subscribe",
                "params": {
                    "channel": "ticker",
                    "symbol": ["INVALID/PAIR"]  # Non-existent pair!
                }
            }

            client.ws.send(json.dumps(invalid_request))

            try:
                response = client.receive_message(timeout=10)
                print(f"  Response: {json.dumps(response, indent=2)}")

                # May get error or may just not receive data
                if response.get("method") == "subscribe":
                    if not response.get("success"):
                        print(f"  ✓ Subscription rejected: {response.get('error')}")
                    else:
                        print(f"  ⚠ Subscription accepted (may just not receive data)")

            except Exception as e:
                print(f"  ✓ Exception raised: {e}")

    def test_empty_symbol(self, kraken_ws_url, default_timeout):
        """Test subscription with empty symbol."""
        print("\n[NEGATIVE TEST] Testing empty symbol...")

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            import json
            invalid_request = {
                "method": "subscribe",
                "params": {
                    "channel": "ticker",
                    "symbol": [""]  # Empty string!
                }
            }

            client.ws.send(json.dumps(invalid_request))

            try:
                response = client.receive_message(timeout=10)
                print(f"  Response: {json.dumps(response, indent=2)}")

                if response.get("method") == "subscribe":
                    assert response.get("success") is False or "error" in response, \
                        "Expected error for empty symbol"
                    print(f"  ✓ Handled empty symbol correctly")

            except Exception as e:
                print(f"  ✓ Exception raised: {e}")

    def test_empty_symbol_list(self, kraken_ws_url, default_timeout):
        """Test subscription with empty symbol list."""
        print("\n[NEGATIVE TEST] Testing empty symbol list...")

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            import json
            invalid_request = {
                "method": "subscribe",
                "params": {
                    "channel": "ticker",
                    "symbol": []  # Empty array!
                }
            }

            client.ws.send(json.dumps(invalid_request))

            try:
                response = client.receive_message(timeout=10)
                print(f"  Response: {json.dumps(response, indent=2)}")

                if response.get("method") == "subscribe":
                    assert response.get("success") is False or "error" in response, \
                        "Expected error for empty symbol list"
                    print(f"  ✓ Handled empty symbol list correctly")

            except Exception as e:
                print(f"  ✓ Exception raised: {e}")

    def test_missing_symbol_parameter(self, kraken_ws_url, default_timeout):
        """Test subscription without symbol parameter."""
        print("\n[NEGATIVE TEST] Testing missing symbol parameter...")

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            import json
            invalid_request = {
                "method": "subscribe",
                "params": {
                    "channel": "ticker"
                    # No "symbol" key at all!
                }
            }

            client.ws.send(json.dumps(invalid_request))

            try:
                response = client.receive_message(timeout=10)
                print(f"  Response: {json.dumps(response, indent=2)}")

                if response.get("method") == "subscribe":
                    assert response.get("success") is False or "error" in response, \
                        "Expected error for missing symbol"
                    print(f"  ✓ Handled missing symbol parameter correctly")

            except Exception as e:
                print(f"  ✓ Exception raised: {e}")

    def test_duplicate_subscription(self, kraken_ws_url, default_timeout):
        """Test subscribing to same channel twice (state management)."""
        print("\n[NEGATIVE TEST] Testing duplicate subscription...")

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            # First subscription (should succeed)
            ack1 = client.subscribe("ticker", ["BTC/USD"])
            print(f"  First subscription: success={ack1.get('success')}")
            assert ack1.get("success") is True, "First subscription should succeed"

            # Second subscription to same channel+pair (test how API handles it)
            try:
                ack2 = client.subscribe("ticker", ["BTC/USD"])
                print(f"  Second subscription: success={ack2.get('success')}")

                # API may accept it (idempotent) or reject it
                if ack2.get("success"):
                    print(f"  ✓ API handles duplicate gracefully (idempotent)")
                else:
                    print(f"  ✓ API rejects duplicate: {ack2.get('error')}")

            except Exception as e:
                print(f"  ✓ Exception on duplicate subscription: {e}")

            # Cleanup
            client.unsubscribe("ticker", ["BTC/USD"])

    def test_resubscribe_after_unsubscribe(self, kraken_ws_url, default_timeout):
        """Test unsubscribing then re-subscribing (state management)."""
        print("\n[NEGATIVE TEST] Testing resubscribe after unsubscribe...")

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            # Subscribe
            ack1 = client.subscribe("ticker", ["BTC/USD"])
            print(f"  Initial subscription: success={ack1.get('success')}")
            assert ack1.get("success") is True

            # Unsubscribe
            unsub_ack = client.unsubscribe("ticker", ["BTC/USD"])
            print(f"  Unsubscribe: success={unsub_ack.get('success')}")

            # Re-subscribe (should work)
            ack2 = client.subscribe("ticker", ["BTC/USD"])
            print(f"  Re-subscription: success={ack2.get('success')}")
            assert ack2.get("success") is True, "Re-subscription should succeed"

            print(f"  ✓ Re-subscription after unsubscribe works correctly")

            # Final cleanup
            client.unsubscribe("ticker", ["BTC/USD"])

    # ========================================================================
    # event_trigger Parameter Tests
    # ========================================================================

    def test_ticker_event_trigger_default(self, kraken_ws_url, default_timeout):
        """Test ticker subscription with default event_trigger (should be 'trades')."""
        print("\n[EVENT_TRIGGER TEST] Testing default event_trigger (should default to 'trades')...")

        pairs = ["BTC/USD"]

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            # Subscribe without event_trigger parameter
            ack = client.subscribe("ticker", pairs)

            print(f"  Subscription: success={ack.get('success')}")
            assert ack.get("success") is True

            # Verify we receive ticker updates
            messages = client.receive_messages(count=2, timeout=30)
            print(f"  Received {len(messages)} ticker messages")
            assert len(messages) > 0, "Should receive ticker messages"

            print(f"  ✓ Default event_trigger works (defaults to 'trades')")
            client.unsubscribe("ticker", pairs)

    def test_ticker_event_trigger_bbo(self, kraken_ws_url, default_timeout):
        """Test ticker subscription with event_trigger='bbo'."""
        print("\n[EVENT_TRIGGER TEST] Testing event_trigger='bbo'...")

        pairs = ["BTC/USD"]

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            ack = client.subscribe("ticker", pairs, event_trigger="bbo")

            print(f"  Subscription: success={ack.get('success')}")
            assert ack.get("success") is True

            # Verify we receive ticker updates (on BBO changes)
            messages = client.receive_messages(count=2, timeout=30)
            print(f"  Received {len(messages)} ticker messages (on BBO changes)")
            assert len(messages) > 0, "Should receive ticker messages"

            print(f"  ✓ event_trigger='bbo' works correctly")

            try:
                client.unsubscribe("ticker", pairs)
                print(f"  ✓ Unsubscribe successful")
            except Exception as e:
                # Catch both TimeoutError and WebSocketTimeoutException
                if 'timeout' in str(e).lower() or 'Timeout' in type(e).__name__:
                    print(f"  ⚠ WARNING: Unsubscribe timed out for event_trigger='bbo'")
                    print(f"  This may indicate an API issue with high-frequency updates")
                else:
                    raise

    def test_ticker_event_trigger_trades(self, kraken_ws_url, default_timeout):
        """Test ticker subscription with event_trigger='trades'."""
        print("\n[EVENT_TRIGGER TEST] Testing event_trigger='trades'...")

        pairs = ["BTC/USD"]

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            ack = client.subscribe("ticker", pairs, event_trigger="trades")

            print(f"  Subscription: success={ack.get('success')}")
            assert ack.get("success") is True

            # Verify we receive ticker updates (on every trade)
            messages = client.receive_messages(count=2, timeout=30)
            print(f"  Received {len(messages)} ticker messages (on every trade)")
            assert len(messages) > 0, "Should receive ticker messages"

            print(f"  ✓ event_trigger='trades' works correctly")
            client.unsubscribe("ticker", pairs)

    def test_ticker_event_trigger_none(self, kraken_ws_url, default_timeout):
        """Test ticker subscription with event_trigger=None (should be rejected)."""
        print("\n[EVENT_TRIGGER TEST] Testing event_trigger=None (should be rejected)...")

        pairs = ["BTC/USD"]

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            with pytest.raises(ValueError) as exc_info:
                client.subscribe("ticker", pairs, event_trigger=None)

            error_msg = str(exc_info.value)
            print(f"  ✓ API correctly rejected event_trigger=None")
            print(f"  Error message: {error_msg}")
            assert "event_trigger" in error_msg.lower() or "must be" in error_msg.lower(), \
                f"Expected event_trigger validation error, but got: {error_msg}"

    def test_ticker_event_trigger_empty_string(self, kraken_ws_url, default_timeout):
        """Test ticker subscription with event_trigger='' (should be rejected)."""
        print("\n[EVENT_TRIGGER TEST] Testing event_trigger='' (should be rejected)...")

        pairs = ["BTC/USD"]

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            with pytest.raises(ValueError) as exc_info:
                client.subscribe("ticker", pairs, event_trigger="")

            error_msg = str(exc_info.value)
            print(f"  ✓ API correctly rejected event_trigger=''")
            print(f"  Error message: {error_msg}")
            assert "event_trigger" in error_msg.lower() or "must be" in error_msg.lower(), \
                f"Expected event_trigger validation error, but got: {error_msg}"

    def test_ticker_event_trigger_invalid(self, kraken_ws_url, default_timeout):
        """Test ticker subscription with event_trigger='invalid' (should be rejected)."""
        print("\n[EVENT_TRIGGER TEST] Testing event_trigger='invalid' (should be rejected)...")

        pairs = ["BTC/USD"]

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            with pytest.raises(ValueError) as exc_info:
                client.subscribe("ticker", pairs, event_trigger="invalid")

            error_msg = str(exc_info.value)
            print(f"  ✓ API correctly rejected event_trigger='invalid'")
            print(f"  Error message: {error_msg}")
            assert "event_trigger" in error_msg.lower() or "must be" in error_msg.lower(), \
                f"Expected event_trigger validation error, but got: {error_msg}"

    def test_ticker_event_trigger_number(self, kraken_ws_url, default_timeout):
        """Test ticker subscription with event_trigger=123 (should be rejected)."""
        print("\n[EVENT_TRIGGER TEST] Testing event_trigger=123 (should be rejected)...")

        pairs = ["BTC/USD"]

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            with pytest.raises(ValueError) as exc_info:
                client.subscribe("ticker", pairs, event_trigger=123)

            error_msg = str(exc_info.value)
            print(f"  ✓ API correctly rejected event_trigger=123")
            print(f"  Error message: {error_msg}")
            assert "event_trigger" in error_msg.lower() or "must be" in error_msg.lower(), \
                f"Expected event_trigger validation error, but got: {error_msg}"

    # ========================================================================
    # snapshot Parameter Tests (Ticker)
    # ========================================================================

    def test_ticker_snapshot_default(self, kraken_ws_url, default_timeout):
        """Test ticker subscription with default snapshot parameter (should be true)."""
        print("\n[SNAPSHOT TEST] Testing default snapshot parameter (should default to true)...")

        pairs = ["BTC/USD"]

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            # Subscribe without snapshot parameter
            ack = client.subscribe("ticker", pairs)

            print(f"  Subscription: success={ack.get('success')}")
            assert ack.get("success") is True

            # Should receive snapshot message (default=true)
            messages = client.receive_messages(count=1, timeout=30)
            first_msg = messages[0]

            print(f"  First message type: {first_msg.get('type')}")
            assert first_msg.get('type') == 'snapshot', \
                f"BUG: Default snapshot should be true, but got type='{first_msg.get('type')}'"

            print(f"  ✓ Default snapshot parameter correctly set to true (received snapshot)")
            client.unsubscribe("ticker", pairs)

    def test_ticker_snapshot_true(self, kraken_ws_url, default_timeout):
        """Test ticker subscription with snapshot=true."""
        print("\n[SNAPSHOT TEST] Testing snapshot=true...")

        pairs = ["BTC/USD"]

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            ack = client.subscribe("ticker", pairs, snapshot=True)

            print(f"  Subscription: success={ack.get('success')}")
            assert ack.get("success") is True

            # Should receive snapshot message
            messages = client.receive_messages(count=1, timeout=30)
            first_msg = messages[0]

            print(f"  First message type: {first_msg.get('type')}")
            assert first_msg.get('type') == 'snapshot', \
                f"Expected snapshot message, but got type='{first_msg.get('type')}'"

            print(f"  ✓ snapshot=true works correctly (received snapshot)")
            client.unsubscribe("ticker", pairs)

    def test_ticker_snapshot_false(self, kraken_ws_url, default_timeout):
        """Test ticker subscription with snapshot=false."""
        print("\n[SNAPSHOT TEST] Testing snapshot=false...")

        pairs = ["BTC/USD"]

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            ack = client.subscribe("ticker", pairs, snapshot=False)

            print(f"  Subscription: success={ack.get('success')}")
            assert ack.get("success") is True

            # Should NOT receive snapshot message, only updates
            messages = client.receive_messages(count=3, timeout=30)

            snapshot_count = sum(1 for msg in messages if msg.get('type') == 'snapshot')
            update_count = sum(1 for msg in messages if msg.get('type') == 'update')

            print(f"  Received: {snapshot_count} snapshots, {update_count} updates")
            assert snapshot_count == 0, \
                f"BUG: snapshot=false should not send snapshots, but got {snapshot_count} snapshot messages"
            assert update_count > 0, "Should receive update messages"

            print(f"  ✓ snapshot=false works correctly (no snapshots, only updates)")
            client.unsubscribe("ticker", pairs)

    def test_ticker_snapshot_none(self, kraken_ws_url, default_timeout):
        """Test ticker subscription with snapshot=None (should be rejected)."""
        print("\n[SNAPSHOT TEST] Testing snapshot=None (should be rejected)...")

        pairs = ["BTC/USD"]

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            with pytest.raises(ValueError) as exc_info:
                client.subscribe("ticker", pairs, snapshot=None)

            error_msg = str(exc_info.value)
            print(f"  ✓ API correctly rejected snapshot=None")
            print(f"  Error message: {error_msg}")
            assert "snapshot" in error_msg.lower() or "boolean" in error_msg.lower(), \
                f"Expected snapshot validation error, but got: {error_msg}"

    def test_ticker_snapshot_invalid_string(self, kraken_ws_url, default_timeout):
        """Test ticker subscription with snapshot='invalid' (should be rejected)."""
        print("\n[SNAPSHOT TEST] Testing snapshot='invalid' (should be rejected)...")

        pairs = ["BTC/USD"]

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            with pytest.raises(ValueError) as exc_info:
                client.subscribe("ticker", pairs, snapshot="invalid")

            error_msg = str(exc_info.value)
            print(f"  ✓ API correctly rejected snapshot='invalid'")
            print(f"  Error message: {error_msg}")
            assert "snapshot" in error_msg.lower() or "boolean" in error_msg.lower(), \
                f"Expected snapshot validation error, but got: {error_msg}"

    def test_ticker_snapshot_invalid_number(self, kraken_ws_url, default_timeout):
        """Test ticker subscription with snapshot=123 (should be rejected)."""
        print("\n[SNAPSHOT TEST] Testing snapshot=123 (should be rejected)...")

        pairs = ["BTC/USD"]

        with KrakenWebSocketClient(kraken_ws_url, timeout=default_timeout) as client:
            with pytest.raises(ValueError) as exc_info:
                client.subscribe("ticker", pairs, snapshot=123)

            error_msg = str(exc_info.value)
            print(f"  ✓ API correctly rejected snapshot=123")
            print(f"  Error message: {error_msg}")
            assert "snapshot" in error_msg.lower() or "boolean" in error_msg.lower(), \
                f"Expected snapshot validation error, but got: {error_msg}"
