FROM python:3.12-slim

WORKDIR /app

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    DOUBAO_HOST=0.0.0.0 \
    DOUBAO_PORT=9090 \
    DOUBAO_HEADLESS=true \
    DOUBAO_AUTO_OPEN=false \
    DOUBAO_BROWSER_DATA=/app/data/doubao_browser

# Install system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser and OS dependencies for Chromium
RUN playwright install --with-deps chromium

# Copy application source code
COPY doubao2api/ doubao2api/

# Ensure persistent data directory exists
RUN mkdir -p /app/data/doubao_browser

EXPOSE 9090

VOLUME ["/app/data"]

CMD ["python", "-m", "doubao2api"]
