# WebSocket API v2 Test Suite

Automated test suite for WebSocket API v2 public channels (Ticker, Book, OHLC, Trade) with comprehensive data validation, HTML reporting, and code coverage analysis.

**Features:**
- 44 test cases across 4 channels with positive/negative scenarios
- JSON schema validation and data integrity checks
- HTML test reports with coverage analysis
- Docker support for containerized execution
- Continuous testing mode for monitoring

See [NOTES.md](NOTES.md) for detailed test scenarios and validation logic.

---

## 📦 Requirements

**Choose one:**
- **Docker** 20.10+ (recommended - no Python needed on host)
- **Python** 3.11+ (for local execution)

---

## 🔧 Installation

### Local Setup

```bash
# Clone repository
git clone <repository-url>
cd <project-root-folder>

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Docker Setup

```bash
# Build image (first time only)
docker build -t kraken-tests .
```

---

## 🚀 Usage

### Local Testing

```bash
# Run all tests with live outputs and status results
pytest -v 

# Run all tests with live outputs and detailed bug logs
pytest -v -s

# Run specific channel
pytest -v tests/test_ticker.py
pytest -v tests/test_book.py
pytest -v tests/test_ohlc.py
pytest -v tests/test_trade.py

# Run with HTML report, coverage and detailed logs (RECOMMENDED)
pytest -v -s --html=reports/report.html --self-contained-html --cov=utils --cov-report=html:reports/coverage --cov-report=term-missing
```

### Docker Testing

```bash
# Run ALL tests (~13 minutes)
docker-compose --profile once up

# Run specific channel (faster)
TEST_PATH=tests/test_ticker.py docker-compose --profile custom up  # ~3 min
TEST_PATH=tests/test_book.py docker-compose --profile custom up    # ~2 min
TEST_PATH=tests/test_ohlc.py docker-compose --profile custom up    # ~8 min
TEST_PATH=tests/test_trade.py docker-compose --profile custom up   # ~3 min

# Run single test (fastest)
TEST_PATH="tests/test_ticker.py::TestTickerChannel::test_ticker_complete_flow" docker-compose --profile custom up

# Continuous testing (runs every 5 minutes by default)
docker-compose --profile loop up

# Continuous testing with custom delay
TEST_DELAY_MINUTES=10 docker-compose --profile loop up

# Run in background
docker-compose --profile loop up -d

# Stop background tests
docker-compose --profile loop down
```

---

## 📊 Test Reports

After running tests, reports are auto-generated in the `reports/` folder:

| Report | Location | Description |
|--------|----------|-------------|
| **Test Results** | `reports/report.html` | Pass/fail status, errors, execution time |
| **Code Coverage** | `reports/coverage/index.html` | Line-by-line coverage analysis (~92% for websocket_client.py) |

### Viewing Reports

**Windows:**
```bash
start reports\report.html
start reports\coverage\index.html
```

**Linux/Mac:**
```bash
open reports/report.html
open reports/coverage/index.html
```

---

## 📁 Project Structure

```
root/
├── schemas/              # JSON validation schemas
├── tests/                # Test files (44 tests across 4 channels)
├── utils/                # WebSocket client utilities
├── reports/              # Auto-generated HTML reports
├── requirements.txt      # Python dependencies
├── Dockerfile            # Docker image definition
├── docker-compose.yml    # Docker orchestration (3 profiles: once, loop, custom)
├── run_tests_loop.sh     # Continuous testing script
├── README.md             # This file
└── NOTES.md              # Detailed test documentation
```

---

## ⚙️ Configuration

Environment variables for Docker testing:

```bash
TEST_PATH="tests/test_ticker.py"    # Specify test file/path
TEST_DELAY_MINUTES=5                # Loop mode delay (default: 5)
PYTEST_ARGS="-v --maxfail=3"        # Additional pytest arguments
```

---

## 📖 Documentation

- **[NOTES.md](NOTES.md)** - Detailed test scenarios, validation logic, and channel-specific behaviors
- **[requirements.txt](requirements.txt)** - Python dependencies (pytest, websocket-client, jsonschema, coverage tools)
