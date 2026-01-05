# WebSocket API v2 Test Suite

Comprehensive test suite for validating WebSocket API v2 public channels with real-time monitoring, HTML reporting, and continuous testing capabilities.

## 🎯 Features

- ✅ **44 Test Cases** across 4 channels (Ticker, Book, OHLC, Trade)
- ✅ **Positive & Negative Scenarios** - Full coverage of success and error cases
- ✅ **Data Integrity Validation** - Mathematical, temporal, and business logic checks
- ✅ **JSON Schema Validation** - Automatic message structure verification
- ✅ **HTML Test Reports** - Self-contained reports with pass/fail details
- ✅ **Code Coverage** - Coverage reports showing tested code paths
- ✅ **Continuous Testing** - Run tests in a loop with configurable delays
- ✅ **Docker Support** - Containerized execution for consistency
- ✅ **Multiple Execution Modes** - Local, Docker single-run, Docker loop, custom tests

## 📋 Test Coverage Summary

| Channel | Tests | Positive | Negative | Data Validations |
|---------|-------|----------|----------|------------------|
| **Ticker** | 11 | 10 | 1 | 9 checks per message |
| **Book** | 12 | 10 | 2 | 6 checks per snapshot |
| **OHLC** | 10 | 8 | 2 | 9 checks per candle |
| **Trade** | 11 | 10 | 1 | 7 checks per trade |
| **Total** | **44** | **38** | **6** | **31 unique checks** |

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Build image (first time only)
docker build -t kraken-tests .

# Run ALL tests (~13 minutes)
docker-compose --profile once up

# Run specific channel tests (faster)
TEST_PATH=tests/test_ticker.py docker-compose --profile custom up  # ~3 minutes
TEST_PATH=tests/test_book.py docker-compose --profile custom up
TEST_PATH=tests/test_ohlc.py docker-compose --profile custom up
TEST_PATH=tests/test_trade.py docker-compose --profile custom up

# View reports
start reports/report.html              # Test results
start reports/coverage/index.html      # Coverage report
```

### Option 2: Local Python

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest -v

# Run specific channel
pytest -v tests/test_ticker.py

# Run with HTML report and coverage (RECOMMENDED)
pytest -v -s --html=reports/report.html --self-contained-html --cov=utils --cov-report=html:reports/coverage --cov-report=term-missing

# View reports
start reports/report.html              # Test results
start reports/coverage/index.html      # Coverage report
```

## 📦 Requirements

Choose one:
- **Docker**: 20.10+ (for containerized execution - no Python needed on host)
- **OR**
- **Python**: 3.11+ (for local execution without Docker)

## 🔧 Installation

### Local Development Setup

```bash
# Clone repository
git clone <repository-url>
cd Kraken

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Docker Setup

```bash
# Build Docker image
docker build -t kraken-tests .

# Verify build
docker images | grep kraken-tests
```

## 🎮 Usage

### Running Tests Locally

#### Run All Tests
```bash
# Basic run
pytest -v

# With live output (see all print statements)
pytest -v -s
```

#### Run Specific Channel
```bash
pytest -v tests/test_ticker.py    # Ticker tests only
pytest -v tests/test_book.py      # Book tests only
pytest -v tests/test_ohlc.py      # OHLC tests only
pytest -v tests/test_trade.py     # Trade tests only
```

#### Run Specific Test
```bash
pytest -v tests/test_ticker.py::TestTickerChannel::test_ticker_data_integrity
```

#### Run with HTML Report
```bash
pytest -v \
  --html=reports/report.html \
  --self-contained-html \
  --cov=. \
  --cov-report=html:reports/coverage
```

#### Run with Live Output
```bash
pytest -v -s  # Shows print statements in real-time
```

#### Run in Parallel (faster)
```bash
pytest -v -n auto  # Uses pytest-xdist for parallel execution
```

### Running Tests in Docker

#### Run All Tests (~13 minutes)
```bash
docker-compose --profile once up
```

#### Run Specific Channel Tests (Faster ⚡)
```bash
# Ticker tests (29 tests, ~3 minutes)
TEST_PATH=tests/test_ticker.py docker-compose --profile custom up

# Book tests (12 tests, ~2 minutes)
TEST_PATH=tests/test_book.py docker-compose --profile custom up

# OHLC tests (10 tests, ~8 minutes)
TEST_PATH=tests/test_ohlc.py docker-compose --profile custom up

# Trade tests (11 tests, ~3 minutes)
TEST_PATH=tests/test_trade.py docker-compose --profile custom up
```

#### Run Single Test (Fastest 🚀)
```bash
TEST_PATH="tests/test_ticker.py::TestTickerChannel::test_ticker_complete_flow" docker-compose --profile custom up
```

#### Continuous Testing (Loop Mode)
```bash
# Run tests every 5 minutes (default)
docker-compose --profile loop up

# Custom delay (10 minutes)
TEST_DELAY_MINUTES=10 docker-compose --profile loop up

# Run in background
docker-compose --profile loop up -d

# Stop background tests
docker-compose --profile loop down
```

#### Custom Test Execution
```bash
# Run specific test file
TEST_PATH=tests/test_ticker.py docker-compose --profile custom up

# Run with custom pytest arguments
PYTEST_ARGS="-v -k data_integrity" docker-compose --profile custom up

# Run specific channel with custom args
TEST_PATH=tests/test_book.py PYTEST_ARGS="-v -s" docker-compose --profile custom up
```

#### Shell Script for Continuous Testing
```bash
# Make script executable (first time only)
chmod +x run_tests_loop.sh

# Run continuous tests locally
./run_tests_loop.sh

# With custom delay (10 minutes)
TEST_DELAY_MINUTES=10 ./run_tests_loop.sh
```

## 📊 Test Reports

### Reports Generated After Each Run

Both reports are auto-generated in `reports/` folder:

| Report | Location | Description |
|--------|----------|-------------|
| **Test Results** | `reports/report.html` | Pass/Fail for each test, errors, timing |
| **Code Coverage** | `reports/coverage/index.html` | Code coverage with line-by-line details |

### View Reports (Windows)

```bash
# Test results report
start reports\report.html

# Coverage report
start reports\coverage\index.html
```

### View Reports (Linux/Mac)

```bash
# Test results report
open reports/report.html

# Coverage report
open reports/coverage/index.html
```

### Coverage Details

**Current Coverage: ~92%** for `utils/websocket_client.py` ✅

Coverage shows:
- 🟢 **Green lines** = Tested code
- 🔴 **Red lines** = Untested code (error handlers, edge cases)
- 📊 **92% is excellent!** - Remaining 8% is mostly error handling

**Note:** Total coverage shows ~35% because it includes unused utility files (helpers.py, recorder.py, validators.py). Focus on `websocket_client.py` which is 92%.

## 🧪 Test Execution Modes

### 1. Development Mode
**When**: Active development, debugging tests
```bash
pytest -v -s tests/test_ticker.py::TestTickerChannel::test_ticker_data_integrity
```
**Features**: Live output, single test, fast feedback

### 2. Full Validation Mode
**When**: Pre-commit, verification of all functionality
```bash
pytest -v --html=reports/report.html --self-contained-html
```
**Features**: All tests, HTML report, complete validation

### 3. Continuous Monitoring Mode
**When**: Production monitoring, regression detection
```bash
docker-compose --profile loop up -d
```
**Features**: Runs forever, timestamped reports, automatic retries

### 4. CI/CD Mode
**When**: Automated pipeline execution
```bash
docker run --rm kraken-tests pytest -v --tb=short --maxfail=5
```
**Features**: Exit on failures, short traceback, containerized

## 📁 Project Structure

```
Kraken/
├── schemas/                    # JSON schemas for validation
│   ├── ticker_schema.json     # Ticker message schema
│   ├── book_schema.json       # Book message schema
│   ├── candles_schema.json    # OHLC message schema
│   └── trade_schema.json      # Trade message schema
│
├── tests/                     # Test files (44 total tests)
│   ├── conftest.py           # Pytest fixtures
│   ├── test_ticker.py        # Ticker tests (11 tests)
│   ├── test_book.py          # Book tests (12 tests)
│   ├── test_ohlc.py          # OHLC tests (10 tests)
│   └── test_trade.py         # Trade tests (11 tests)
│
├── utils/                     # Shared utilities
│   └── websocket_client.py   # WebSocket wrapper
│
├── reports/                   # Auto-generated reports
│   ├── report.html           # Latest test report
│   └── coverage/             # Coverage HTML report
│
├── requirements.txt           # Python dependencies
├── Dockerfile                # Docker image definition
├── docker-compose.yml        # Docker orchestration
├── run_tests_loop.sh         # Continuous testing script
├── .dockerignore             # Docker build exclusions
├── README.md                 # This file
└── NOTES.md                  # Detailed test documentation
```

## 🔍 What Each Channel Tests

### Ticker Channel (11 tests)
- ✅ Subscription lifecycle
- ✅ Schema validation
- ✅ Snapshot behavior (default, true, false)
- ✅ Multiple symbols
- ✅ Data integrity (9 validations):
  - Bid/ask/last prices > 0
  - Bid < ask (no crossed spread)
  - Volume > 0, VWAP > 0
  - Low <= high
- ❌ Invalid symbol handling

### Book Channel (12 tests)
- ✅ Subscription lifecycle
- ✅ Schema validation
- ✅ Depth parameter (default=10, custom=25)
- ✅ Snapshot and update messages
- ✅ Checksum validation
- ✅ Data integrity (6 validations):
  - **Best bid < best ask (STRICT - fails test if violated)**
  - Bids descending, asks ascending
  - Non-empty order book
- ❌ Invalid symbol/depth handling

### OHLC/Candles Channel (10 tests)
- ✅ Subscription lifecycle
- ✅ Schema validation
- ✅ Interval parameter (default=1, custom=5)
- ✅ Snapshot behavior
- ✅ Data integrity (9 validations):
  - OHLC relationships: low <= open, close <= high
  - Prices > 0, volume >= 0, trades >= 0
  - Interval matching
  - Timestamp ordering and intervals
- ❌ Invalid symbol/interval handling

### Trade Channel (11 tests)
- ✅ Subscription lifecycle
- ✅ Schema validation
- ✅ Snapshot behavior (default=false, can request last 50)
- ✅ Multiple symbols
- ✅ Trade ID sequence
- ✅ Data integrity (7 validations):
  - Price > 0, quantity > 0
  - Side in ['buy', 'sell']
  - Order type in ['limit', 'market']
  - Valid timestamps
- ❌ Invalid symbol handling

## ⚙️ Configuration

### Environment Variables

```bash
# Continuous testing delay (minutes)
TEST_DELAY_MINUTES=5

# Custom pytest arguments
PYTEST_ARGS="--maxfail=3 -v"

# Custom test path
TEST_PATH="tests/test_ticker.py"
```

### Pytest Configuration

Create `pytest.ini` (optional):
```ini
[pytest]
minversion = 8.0
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```
