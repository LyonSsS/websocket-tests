import pytest
import json
import os
from pathlib import Path


@pytest.fixture(scope="session")
def kraken_ws_url():
    """Kraken WebSocket API v2 endpoint."""
    return "wss://ws.kraken.com/v2"


@pytest.fixture(scope="session")
def schemas_dir():
    """Path to schemas directory."""
    return Path(__file__).parent.parent / "schemas"


@pytest.fixture
def load_schema(schemas_dir):
    """Factory fixture to load JSON schemas."""
    def _load_schema(schema_name):
        schema_path = schemas_dir / f"{schema_name}_schema.json"
        if not schema_path.exists():
            pytest.skip(f"Schema file {schema_name}_schema.json not found")
        with open(schema_path, 'r') as f:
            return json.load(f)
    return _load_schema


@pytest.fixture
def default_timeout():
    """Default timeout for WebSocket operations in seconds."""
    return 30
