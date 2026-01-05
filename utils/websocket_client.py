import json
import time
import websocket
from typing import Dict, List, Optional, Any


class KrakenWebSocketClient:
    """
    WebSocket client wrapper for Kraken API with built-in validation.

    This client handles:
    - Connection management
    - Subscription acknowledgment validation
    - Message buffering
    - Automatic cleanup
    """

    def __init__(self, url: str, timeout: int = 30):
        """
        Initialize WebSocket client.

        Args:
            url: WebSocket endpoint URL
            timeout: Timeout for operations in seconds
        """
        self.url = url
        self.timeout = timeout
        self.ws: Optional[websocket.WebSocket] = None
        self.messages: List[Dict] = []

    def connect(self) -> None:
        """Establish WebSocket connection."""
        self.ws = websocket.create_connection(self.url, timeout=self.timeout)

    def disconnect(self) -> None:
        """Close WebSocket connection."""
        if self.ws:
            self.ws.close()
            self.ws = None

    def subscribe(self, channel: str, symbol: List[str], **options) -> Dict:
        """
        Subscribe to a channel and validate acknowledgment (WebSocket v2 API).

        Args:
            channel: Channel name (e.g., 'ticker', 'book', 'ohlc', 'trade')
            symbol: List of currency pairs (e.g., ['BTC/USD'])
            **options: Additional subscription options (e.g., depth=10, interval=1)

        Returns:
            Subscription acknowledgment message

        Raises:
            ValueError: If subscription fails or acknowledgment is invalid
        """
        if not self.ws:
            raise RuntimeError("Not connected. Call connect() first.")

        # v2 API format
        params = {
            "channel": channel,
            "symbol": symbol
        }
        params.update(options)

        request = {
            "method": "subscribe",
            "params": params
        }

        self.ws.send(json.dumps(request))

        # Wait for subscription acknowledgment (v2 format)
        ack = self._wait_for_method("subscribe")

        # Validate acknowledgment
        if not ack.get("success"):
            error = ack.get("error", "Unknown error")
            raise ValueError(f"Subscription failed: {error}")

        return ack

    def _wait_for_method(self, method: str, timeout: Optional[int] = None) -> Dict:
        """
        Wait for a specific method response (v2 API).

        Args:
            method: Method name to wait for (e.g., 'subscribe', 'unsubscribe')
            timeout: Optional timeout override

        Returns:
            Method response message
        """
        start_time = time.time()
        effective_timeout = timeout or self.timeout

        while True:
            elapsed = time.time() - start_time
            if elapsed > effective_timeout:
                raise TimeoutError(f"Timeout waiting for method: {method}")

            remaining = effective_timeout - elapsed
            msg = self.receive_message(timeout=remaining)

            if isinstance(msg, dict) and msg.get("method") == method:
                return msg

    def unsubscribe(self, channel: str, symbol: List[str], **options) -> Dict:
        """
        Unsubscribe from a channel and validate acknowledgment (WebSocket v2 API).

        Args:
            channel: Channel name
            symbol: List of currency pairs
            **options: Additional subscription options

        Returns:
            Unsubscription acknowledgment message
        """
        if not self.ws:
            raise RuntimeError("Not connected. Call connect() first.")

        # v2 API format
        params = {
            "channel": channel,
            "symbol": symbol
        }
        params.update(options)

        request = {
            "method": "unsubscribe",
            "params": params
        }

        self.ws.send(json.dumps(request))

        # Wait for unsubscription acknowledgment
        ack = self._wait_for_method("unsubscribe")

        return ack

    def receive_message(self, timeout: Optional[int] = None) -> Dict:
        """
        Receive a single message from WebSocket.

        Args:
            timeout: Optional timeout override

        Returns:
            Parsed JSON message
        """
        if not self.ws:
            raise RuntimeError("Not connected. Call connect() first.")

        original_timeout = self.ws.gettimeout()
        try:
            if timeout is not None:
                self.ws.settimeout(timeout)
            data = self.ws.recv()
            message = json.loads(data)
            return message
        finally:
            self.ws.settimeout(original_timeout)

    def receive_messages(self, count: int = 10, timeout: Optional[int] = None) -> List[Dict]:
        """
        Receive multiple messages.

        Args:
            count: Number of messages to receive
            timeout: Timeout for entire operation

        Returns:
            List of parsed messages
        """
        messages = []
        start_time = time.time()
        effective_timeout = timeout or self.timeout

        while len(messages) < count:
            elapsed = time.time() - start_time
            if elapsed > effective_timeout:
                raise TimeoutError(f"Timeout receiving messages. Got {len(messages)}/{count}")

            remaining = effective_timeout - elapsed
            try:
                msg = self.receive_message(timeout=remaining)
                # Filter out heartbeat messages (v2 API uses "heartbeat" channel)
                if isinstance(msg, dict) and msg.get("channel") == "heartbeat":
                    continue
                # Filter out status messages
                if isinstance(msg, dict) and msg.get("channel") == "status":
                    continue
                # Filter out method response messages (subscribe/unsubscribe acknowledgments)
                if isinstance(msg, dict) and msg.get("method") in ["subscribe", "unsubscribe"]:
                    continue
                messages.append(msg)
            except Exception as e:
                if len(messages) > 0:
                    # Got some messages, return what we have
                    break
                raise

        return messages

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.disconnect()
        return False
