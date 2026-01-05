#!/usr/bin/env python3
"""
Demo script showing how to use the Kraken WebSocket v2 client.

This demonstrates the complete flow:
1. Connect to Kraken WebSocket API v2
2. Subscribe with automatic acknowledgment validation
3. Receive and display ticker data
4. Unsubscribe with automatic acknowledgment validation
5. Verify no more data arrives (proves unsubscription worked)
6. Proper cleanup

Run with: python demo_websocket.py
"""

import json
import time
from utils.websocket_client import KrakenWebSocketClient
from utils.validators import validate_schema


def main():
    """Demo: Complete subscription flow with BTC/USD and SOL/USD ticker."""

    print("\n" + "=" * 70)
    print(" Kraken WebSocket v2 API - Ticker Channel Demo")
    print("=" * 70 + "\n")

    # Endpoint
    url = "wss://ws.kraken.com/v2"
    pairs = ["BTC/USD", "SOL/USD"]

    print(f"Endpoint: {url}")
    print(f"Channel: ticker")
    print(f"Pairs: {', '.join(pairs)}")
    print()

    try:
        # Create client (using context manager for auto-cleanup)
        with KrakenWebSocketClient(url, timeout=30) as client:

            # STEP 1: Connect
            print("-" * 70)
            print("STEP 1: CONNECTION")
            print("-" * 70)
            print(f"✓ Connected to {url}")
            print()

            # STEP 2: Subscribe (with automatic validation)
            print("-" * 70)
            print("STEP 2: SUBSCRIBE (with automatic acknowledgment validation)")
            print("-" * 70)
            print(f"Subscribing to ticker for {', '.join(pairs)}...")
            print()

            try:
                # Validation happens automatically inside subscribe()
                # If it fails, we'll get a ValueError exception
                ack = client.subscribe("ticker", pairs)

                print("✓ Subscription successful!")
                print(f"  Channel: {ack.get('result', {}).get('channel')}")
                print(f"  Symbol: {ack.get('result', {}).get('symbol')}")
                print(f"  Event Trigger: {ack.get('result', {}).get('event_trigger')}")
                print(f"  Server Response Time: {ack.get('time_in')}")
                print()
                print("  (Acknowledgment validation passed)")

            except ValueError as e:
                print(f"✗ Subscription failed: {e}")
                return
            print()

            # STEP 3: Receive data
            print("-" * 70)
            print("STEP 3: RECEIVE DATA")
            print("-" * 70)
            print("Receiving ticker messages...")
            print()

            messages = client.receive_messages(count=5, timeout=30)
            print(f"✓ Received {len(messages)} messages\n")

            for i, msg in enumerate(messages, 1):
                print(f"Message {i}:")
                print(f"  Channel: {msg.get('channel')}")
                print(f"  Type: {msg.get('type')}")

                if msg.get('data'):
                    for ticker in msg['data']:
                        symbol = ticker.get('symbol')
                        bid = ticker.get('bid')
                        ask = ticker.get('ask')
                        last = ticker.get('last')
                        volume = ticker.get('volume')
                        high = ticker.get('high')
                        low = ticker.get('low')

                        print(f"\n  {symbol} Ticker Data:")
                        print(f"    Bid:    ${bid:,.2f}")
                        print(f"    Ask:    ${ask:,.2f}")
                        print(f"    Last:   ${last:,.2f}")
                        print(f"    High:   ${high:,.2f}")
                        print(f"    Low:    ${low:,.2f}")
                        print(f"    Volume: {volume:,.4f}")
                print()

            # STEP 4: Unsubscribe (with automatic validation)
            print("-" * 70)
            print("STEP 4: UNSUBSCRIBE (with automatic acknowledgment validation)")
            print("-" * 70)
            print(f"Unsubscribing from ticker for {', '.join(pairs)}...")
            print()

            try:
                # Validation happens automatically inside unsubscribe()
                unsubscribe_ack = client.unsubscribe("ticker", pairs)

                print("✓ Unsubscription successful!")
                print(f"  Channel: {unsubscribe_ack.get('result', {}).get('channel')}")
                print(f"  Symbol: {unsubscribe_ack.get('result', {}).get('symbol')}")
                print(f"  Server Response Time: {unsubscribe_ack.get('time_in')}")
                print()
                print("  (Unsubscription acknowledgment validation passed)")

            except ValueError as e:
                print(f"✗ Unsubscription failed: {e}")
            print()

            # STEP 5: Verify no more data (proves unsubscription worked)
            print("-" * 70)
            print("STEP 5: VERIFY NO MORE DATA (validate unsubscription)")
            print("-" * 70)
            print("Waiting 20 seconds to verify no more ticker messages arrive...")
            print("(This proves unsubscription actually worked)")
            print()

            # Try to receive messages - should get none or timeout
            try:
                # Lower timeout per message, but try for 20 seconds total
                start_time = time.time()
                unexpected_messages = []

                while time.time() - start_time < 20:
                    try:
                        msg = client.receive_message(timeout=5)
                        # If we get here, we received a message (unexpected!)
                        if msg.get('channel') == 'ticker':
                            unexpected_messages.append(msg)
                            print(f"  ✗ WARNING: Still receiving ticker data: {msg.get('type')}")
                    except:
                        # Timeout is expected - no messages coming
                        pass

                    # Show progress
                    elapsed = int(time.time() - start_time)
                    print(f"  Waiting... {elapsed}/20 seconds", end='\r')

                print()  # New line after progress

                if not unexpected_messages:
                    print("✓ No ticker messages received for 20 seconds")
                    print("  Unsubscription verified - no more data flowing!")
                else:
                    print(f"✗ Still received {len(unexpected_messages)} ticker messages")
                    print("  Unsubscription may not have worked properly")

            except Exception as e:
                print(f"  Check completed with timeout (this is expected)")
            print()

        # Connection automatically closed by context manager
        print("-" * 70)
        print("STEP 6: CLEANUP")
        print("-" * 70)
        print("✓ Connection closed (automatic cleanup)")
        print()

        print("=" * 70)
        print(" Demo completed successfully!")
        print("=" * 70 + "\n")

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\n\n✗ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
