# Dota Themer - Docker Configuration
# Multi-stage build for smaller final image

# Build stage
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies into a venv with uv
RUN uv venv /app/.venv \
    && uv pip install --python /app/.venv/bin/python -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash dota-themer

# Copy the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Put the venv on PATH
ENV PATH=/app/.venv/bin:$PATH

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
CMD ["/app/.venv/bin/python", "bot.py"]

# Alternative: run core.py for CLI testing
# CMD ["/app/.venv/bin/python", "core.py", "2"]
