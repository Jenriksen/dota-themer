# Dota Themer - Docker Configuration
# Multi-stage build for smaller final image

# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash dota-themer

# Copy installed packages from builder
COPY --from=builder /root/.local /home/dota-themer/.local

# Make sure scripts in .local are usable
ENV PATH=/home/dota-themer/.local/bin:$PATH

# Copy application code
COPY --chown=dota-themer:dota-themer . .

# Create logs directory
RUN mkdir -p /app/logs && chown dota-themer:dota-themer /app/logs

# Switch to non-root user
USER dota-themer

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_LEVEL=INFO \
    LOG_FORMAT=json \
    LOG_FILE=/app/logs/dota-themer.log

# Expose port (for potential web interface in future)
EXPOSE 8080

# Default command: run the Discord bot
CMD ["python", "bot.py"]

# Alternative: run core.py for CLI testing
# CMD ["python", "core.py", "2"]
