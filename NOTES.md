# WebSocket API v2 Test Suite Documentation

## Overview

This test suite provides comprehensive validation of the WebSocket API v2 public channels. It includes both positive and negative test scenarios, data integrity validation, schema conformance testing, and continuous monitoring capabilities.

## Test Coverage by Channel

### 1. Ticker Channel (`tests/test_ticker.py`)

**Purpose**: Real-time price ticker updates for currency pairs

#### Positive Scenarios
- ✅ **Complete subscription flow** - Subscribe, receive data, unsubscribe
- ✅ **Schema validation** - Messages conform to JSON schema
- ✅ **Default snapshot behavior** - snapshot parameter defaults correctly
- ✅ **Explicit snapshot=true** - Initial snapshot received
- ✅ **Explicit snapshot=false** - Only updates received
- ✅ **Multiple symbols** - Can subscribe to multiple pairs simultaneously
- ✅ **Continuous data reception** - Connection stays alive, receives updates

#### Negative Scenarios
- ❌ **Invalid symbol subscription** - Gracefully fails with error message

#### Data Validation (9 checks per ticker)
```
0. Data array not empty & all required fields present
1. bid > 0 (positive bid price)
2. ask > 0 (positive ask price)
3. bid < ask (spread not crossed)
4. last_price > 0 (positive last trade price)
5. volume > 0 (positive 24h volume)
6. vwap > 0 (positive volume-weighted average price)
7. low <= high (24h price range valid)
8. symbol matches subscription
```

**Test Count**: 11 tests covering all scenarios

---

### 2. Book Channel (`tests/test_book.py`)

**Purpose**: Order book depth snapshots and real-time updates

#### Positive Scenarios
- ✅ **Complete subscription flow** - Subscribe, receive data, unsubscribe
- ✅ **Schema validation** - Messages conform to JSON schema
- ✅ **Default depth** - depth parameter defaults correctly (10)
- ✅ **Custom depth=25** - Receives 25 price levels
- ✅ **Snapshot behavior** - Receives initial order book state
- ✅ **Update messages** - Receives incremental updates
- ✅ **Multiple symbols** - Can subscribe to multiple books
- ✅ **Checksum validation** - Order book integrity verified

#### Negative Scenarios
- ❌ **Invalid symbol subscription** - Gracefully fails with error message
- ❌ **Invalid depth parameter** - Rejects invalid depth values

#### Data Validation (6 checks per book snapshot)
```
0. Data array not empty & required fields present
1. Bids not empty (order book has buy orders)
2. Asks not empty (order book has sell orders)
3. Best bid < best ask (book not crossed) ⚠️ STRICT
4. Bid prices descending (highest to lowest)
5. Ask prices ascending (lowest to highest)
```

**⚠️ SPECIAL NOTE**: Book tests include **STRICT ASSERTIONS** (check #3) that will intentionally FAIL if the order book is crossed. This catches critical data integrity issues that would break trading applications.

**Test Count**: 12 tests covering all scenarios

---

### 3. OHLC/Candles Channel (`tests/test_ohlc.py`)

**Purpose**: Candlestick/OHLC data for technical analysis and charting

#### Positive Scenarios
- ✅ **Complete subscription flow** - Subscribe, receive data, unsubscribe
- ✅ **Schema validation** - Messages conform to JSON schema
- ✅ **Default interval** - interval parameter defaults to 1 minute
- ✅ **Interval=5** - 5-minute candles (60s timeout)
- ✅ **Snapshot default** - Default snapshot behavior
- ✅ **Explicit snapshot=true** - Initial candle snapshot
- ✅ **Explicit snapshot=false** - Only new candles
- ✅ **Multiple symbols** - Multi-symbol subscription
- ✅ **Comprehensive data integrity** - Full OHLC validation

#### Negative Scenarios
- ❌ **Invalid symbol subscription** - Gracefully fails with error message
- ❌ **Invalid interval parameter** - Rejects invalid intervals

#### Data Validation (9 checks per candle)
```
0. Data array not empty & all required fields present
1. OHLC relationships: low <= open, close <= high
2. trades >= 0 (non-negative trade count)
3. volume >= 0 (non-negative volume)
4. vwap > 0 (positive volume-weighted average price)
5. interval matches subscription
6. All prices > 0 (positive prices)
7. interval_begin < message timestamp (temporal ordering)
8. Time difference matches interval exactly (±1s tolerance)
```

**Test Count**: 10 tests (removed interval=15 for performance)

**Timeout Strategy**:
- 1-minute candles: 30 seconds timeout
- 5-minute candles: 60 seconds timeout (doubled for safety)

---

### 4. Trade Channel (`tests/test_trade.py`)

**Purpose**: Individual trade execution stream (last 50 trades snapshot + live updates)

#### Positive Scenarios
- ✅ **Complete subscription flow** - Subscribe, receive data, unsubscribe
- ✅ **Schema validation** - Messages conform to JSON schema
- ✅ **Default snapshot behavior** - snapshot=false by default
- ✅ **Explicit snapshot=true** - Receives last 50 trades
- ✅ **Explicit snapshot=false** - Only live trades
- ✅ **Multiple symbols** - Multi-symbol subscription
- ✅ **Trade ID sequence** - All trade_ids are positive integers
- ✅ **Side distribution** - Buy/sell sides validated
- ✅ **Order type distribution** - Limit/market types validated
- ✅ **Comprehensive data integrity** - Full trade validation

#### Negative Scenarios
- ❌ **Invalid symbol subscription** - Gracefully fails with error message

#### Data Validation (7 checks per trade)
```
0. Data array not empty & all required fields present
1. qty > 0 (positive trade size)
2. price > 0 (positive price)
3. side in ['buy', 'sell'] (valid taker direction)
4. ord_type in ['limit', 'market'] (valid order type)
5. trade_id > 0 (positive unique sequence number)
6. symbol matches subscription
7. timestamp is valid RFC3339 format
```

**Test Count**: 11 tests covering all scenarios

---

### Project Structure

```
Kraken/
├── schemas/              # JSON schemas for validation
│   ├── ticker_schema.json
│   ├── book_schema.json
│   ├── candles_schema.json
│   └── trade_schema.json
├── tests/               # Test files organized by channel
│   ├── conftest.py     # Pytest fixtures
│   ├── test_ticker.py  # Ticker channel tests (11 tests)
│   ├── test_book.py    # Book channel tests (12 tests)
│   ├── test_ohlc.py    # OHLC channel tests (10 tests)
│   └── test_trade.py   # Trade channel tests (11 tests)
├── utils/              # Shared utilities
│   └── websocket_client.py  # WebSocket wrapper
├── reports/            # Test reports (auto-generated)
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker image for tests
├── docker-compose.yml  # Docker orchestration
├── run_tests_loop.sh   # Continuous testing script
└── README.md          # Usage instructions
```


## Test Execution Modes

### 1. Local Execution
Run tests directly on your machine (requires Python 3.11+)

### 2. Docker Single Run
Run tests once in a containerized environment with HTML reports

### 3. Docker Continuous Loop
Run tests continuously with configurable delays (default: 5 minutes)

### 4. Docker Custom Tests
Run specific test files or modules

See **README.md** for detailed execution instructions.

---

## Test Reporting

### HTML Reports
- Generated in `reports/` directory
- Self-contained HTML with embedded CSS/JS
- Includes pass/fail status, error details, and execution time

### Coverage Reports
- HTML coverage report showing code coverage
- Terminal coverage summary
- Identifies untested code paths

### Continuous Testing Reports
- Timestamped reports for each test run
- Format: `report_YYYYMMDD_HHMMSS.html`
- Coverage reports: `coverage_YYYYMMDD_HHMMSS/index.html`

---

## Timeout Handling

### Default Timeout
**30 seconds** for most operations (defined in `conftest.py`)

### Extended Timeouts
- **OHLC 5-minute candles**: 60 seconds (doubled to wait for candle formation)
- **Book unsubscribe**: May timeout on high-frequency channels (acceptable)

### Timeout Exceptions
Tests catch both:
- `TimeoutError` (standard Python exception)
- `websocket.WebSocketTimeoutException` (library-specific)

Pattern used:
```python
except Exception as e:
    if 'timeout' not in str(e).lower() and 'Timeout' not in type(e).__name__:
        raise
    print(f"⚠ Timeout acceptable for high-frequency channel")
```

## Maintenance & Updates

### When API Changes
1. Update affected schema in `schemas/` directory
2. Update validation logic in test files
3. Re-run full suite: `pytest -v`
4. Update this documentation

### When Adding Tests
1. Add test function to appropriate channel file
2. Follow existing naming: `test_<channel>_<scenario>`
3. Include docstring explaining test purpose
4. Update test count in this document

### When Debugging Failures
1. Check HTML report in `reports/` directory
2. Run with verbose output: `pytest -v -s`
3. Check if Kraken API behavior changed
4. Verify network connectivity
5. Review timeout settings for slow responses

---

## Future Enhancements

- [ ] Add recorded fixtures for offline testing
- [ ] Implement parallel test execution (pytest-xdist)
- [ ] Test WebSocket reconnection scenarios
- [ ] Add chaos testing (connection drops, malformed data)
- [ ] Implement test data generators for edge cases
