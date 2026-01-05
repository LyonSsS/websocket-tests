FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create reports directory
RUN mkdir -p /app/reports

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTEST_ARGS=""

# Default command: run tests once with HTML report
CMD pytest -v \
    --html=/app/reports/report.html \
    --self-contained-html \
    --cov=utils \
    --cov-report=html:/app/reports/coverage \
    --cov-report=term-missing \
    ${PYTEST_ARGS}
