#!/bin/bash

# Continuous Testing Script for Kraken WebSocket Tests
# Runs tests in a loop with configurable delay

# Configuration
DELAY_MINUTES=${TEST_DELAY_MINUTES:-5}
DELAY_SECONDS=$((DELAY_MINUTES * 60))
REPORT_DIR="/app/reports"
TIMESTAMP_FORMAT="%Y%m%d_%H%M%S"

echo "========================================="
echo "Kraken WebSocket Continuous Testing"
echo "========================================="
echo "Delay between runs: ${DELAY_MINUTES} minutes"
echo "Reports directory: ${REPORT_DIR}"
echo ""

# Create reports directory if it doesn't exist
mkdir -p "${REPORT_DIR}"

# Test counter
RUN_COUNT=0

# Function to run tests
run_tests() {
    local run_num=$1
    local timestamp=$(date +"${TIMESTAMP_FORMAT}")

    echo ""
    echo "========================================="
    echo "Test Run #${run_num} - $(date)"
    echo "========================================="

    # Run pytest with HTML report
    pytest -v \
        --html="${REPORT_DIR}/report_${timestamp}.html" \
        --self-contained-html \
        --cov=. \
        --cov-report=html:"${REPORT_DIR}/coverage_${timestamp}" \
        --cov-report=term \
        --tb=short \
        ${PYTEST_ARGS}

    local exit_code=$?

    echo ""
    echo "Test run #${run_num} completed with exit code: ${exit_code}"
    echo "Report: ${REPORT_DIR}/report_${timestamp}.html"
    echo "Coverage: ${REPORT_DIR}/coverage_${timestamp}/index.html"

    return ${exit_code}
}

# Trap SIGINT and SIGTERM for graceful shutdown
trap 'echo ""; echo "Shutting down continuous testing..."; exit 0' SIGINT SIGTERM

# Main loop
while true; do
    RUN_COUNT=$((RUN_COUNT + 1))

    run_tests ${RUN_COUNT}

    echo ""
    echo "Next run in ${DELAY_MINUTES} minutes..."
    echo "Press Ctrl+C to stop"

    sleep ${DELAY_SECONDS}
done
