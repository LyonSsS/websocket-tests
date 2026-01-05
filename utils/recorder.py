#!/usr/bin/env python3
"""
Optional recording utility for capturing live WebSocket messages.

This utility connects to Kraken WebSocket API and records sample messages
to the fixtures/ directory for future replay and deterministic testing.

Usage:
    python -m utils.recorder --channel ticker --pair BTC/USD --count 10
    python -m utils.recorder --channel book --pair ETH/USD --count 5 --depth 10
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from websocket_client import KrakenWebSocketClient


def record_messages(channel: str, pair: str, count: int = 10, **options):
    """
    Record messages from a Kraken WebSocket channel.

    Args:
        channel: Channel name (ticker, book, ohlc, trade)
        pair: Currency pair (e.g., BTC/USD)
        count: Number of messages to record
        **options: Additional subscription options
    """
    url = "wss://ws.kraken.com"
    fixtures_dir = Path(__file__).parent.parent / "fixtures"
    fixtures_dir.mkdir(exist_ok=True)

    print(f"Connecting to {url}...")
    print(f"Recording {count} messages from {channel} channel for {pair}")

    if options:
        print(f"Options: {options}")

    try:
        with KrakenWebSocketClient(url) as client:
            # Subscribe
            print("Subscribing...")
            ack = client.subscribe(channel, [pair], **options)
            print(f"Subscription acknowledged: {ack.get('status')}")

            # Save subscription acknowledgment
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ack_filename = f"{channel}_{pair.replace('/', '_')}_subscription_{timestamp}.json"
            ack_path = fixtures_dir / ack_filename
            with open(ack_path, 'w') as f:
                json.dump(ack, f, indent=2)
            print(f"Saved subscription ack to: {ack_filename}")

            # Receive and save messages
            print(f"\nReceiving messages...")
            messages = []
            msg_count = 0

            while msg_count < count:
                msg = client.receive_message()

                # Skip heartbeat messages
                if isinstance(msg, dict) and msg.get("event") == "heartbeat":
                    print(".", end="", flush=True)
                    continue

                # Skip system status messages
                if isinstance(msg, dict) and msg.get("event") == "systemStatus":
                    continue

                messages.append(msg)
                msg_count += 1
                print(f"\n[{msg_count}/{count}] Received message")

            print(f"\nReceived {len(messages)} messages")

            # Save messages
            messages_filename = f"{channel}_{pair.replace('/', '_')}_messages_{timestamp}.json"
            messages_path = fixtures_dir / messages_filename
            with open(messages_path, 'w') as f:
                json.dump(messages, f, indent=2)
            print(f"Saved messages to: {messages_filename}")

            # Unsubscribe
            print("\nUnsubscribing...")
            unsubscribe_ack = client.unsubscribe(channel, [pair], **options)
            print(f"Unsubscription status: {unsubscribe_ack.get('status')}")

            print("\nRecording complete!")
            return messages

    except KeyboardInterrupt:
        print("\n\nRecording interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError during recording: {e}")
        sys.exit(1)


def main():
    """Main entry point for recorder utility."""
    parser = argparse.ArgumentParser(
        description="Record Kraken WebSocket messages to fixtures"
    )
    parser.add_argument(
        "--channel",
        required=True,
        choices=["ticker", "book", "ohlc", "trade"],
        help="Channel to record from"
    )
    parser.add_argument(
        "--pair",
        required=True,
        help="Currency pair (e.g., BTC/USD, ETH/USD)"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of messages to record (default: 10)"
    )
    parser.add_argument(
        "--depth",
        type=int,
        help="Order book depth (for book channel)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        help="Candle interval in minutes (for ohlc channel)"
    )

    args = parser.parse_args()

    # Prepare options
    options = {}
    if args.depth is not None:
        options["depth"] = args.depth
    if args.interval is not None:
        options["interval"] = args.interval

    # Record messages
    record_messages(
        channel=args.channel,
        pair=args.pair,
        count=args.count,
        **options
    )


if __name__ == "__main__":
    main()
