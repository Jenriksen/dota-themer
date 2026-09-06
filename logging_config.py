"""
Dota Themer - Structured Logging Configuration

Provides consistent logging configuration across the application.
Uses Python's built-in logging with JSON formatter for structured output.
"""

import json
import logging
import logging.config
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs log records as JSON.

    This enables structured logging that can be easily parsed by log
    aggregation tools like ELK, Splunk, CloudWatch, etc.
    """

    def __init__(
        self,
        include_timestamp: bool = True,
        include_level: bool = True,
        include_module: bool = True,
    ):
        """
        Initialize the structured formatter.

        Args:
            include_timestamp: Include ISO 8601 timestamp
            include_level: Include log level
            include_module: Include module name
        """
        super().__init__()
        self.include_timestamp = include_timestamp
        self.include_level = include_level
        self.include_module = include_module

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string."""
        log_entry: Dict[str, Any] = {"message": record.getMessage()}

        # Add standard fields
        if self.include_timestamp:
            log_entry["timestamp"] = (
                datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            )

        if self.include_level:
            log_entry["level"] = record.levelname
            log_entry["level_num"] = record.levelno

        if self.include_module:
            log_entry["module"] = record.module
            log_entry["func"] = record.funcName
            log_entry["line"] = record.lineno

        # Add process/thread info
        log_entry["process"] = {
            "id": os.getpid(),
            "name": sys.argv[0] if sys.argv else "dota-themer",
        }

        if record.processName:
            log_entry["process"]["name"] = record.processName

        if record.thread and hasattr(record.thread, "name"):
            thread_id = getattr(record.thread, "ident", None)
            log_entry["thread"] = {
                "id": thread_id,
                "name": record.thread.name,
            }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info),
            }

        # Add extra fields from the record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in (
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "exc_info",
                "exc_text",
                "thread",
                "threadName",
                "message",
                "asctime",
            ):
                try:
                    # Ensure the value is JSON serializable
                    json.dumps(value)
                    extra_fields[key] = value
                except (TypeError, ValueError):
                    extra_fields[key] = str(value)

        if extra_fields:
            log_entry["extra"] = extra_fields

        return json.dumps(log_entry, default=str)


class PlainTextFormatter(logging.Formatter):
    """
    Human-readable formatter for development/console output.

    Format: [TIMESTAMP] LEVEL [MODULE:FUNCTION:LINE] message
    """

    def __init__(self):
        super().__init__(
            fmt="%(asctime)s | %(levelname)-8s | %(module)s:%(funcName)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


# Logger names for different components
LOGGER_CORE = "dota_themer.core"
LOGGER_BOT = "dota_themer.bot"
LOGGER_MAIN = "dota_themer.main"


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Get a logger with the specified name and level.

    Args:
        name: Logger name (e.g., __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
              If None, uses the root logger's level

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    if level is not None:
        logger.setLevel(level)

    return logger


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    log_file: Optional[str] = None,
    console_output: bool = True,
) -> None:
    """
    Configure structured logging for the application.

    Args:
        log_level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Output format ('json' for structured, 'text' for human-readable)
        log_file: Optional path to log file
        console_output: Whether to output logs to console

    Example:
        # For development (human-readable console output)
        setup_logging(log_level="DEBUG", log_format="text")

        # For production (JSON to file and console)
        setup_logging(log_level="INFO", log_format="json",
                      log_file="/var/log/dota-themer/app.log")
    """
    # Convert string level to logging constant
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Choose formatter based on format
    if log_format == "json":
        formatter = StructuredFormatter()
    else:
        formatter = PlainTextFormatter()  # type: ignore[assignment]

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Set levels for specific loggers
    logging.getLogger(LOGGER_CORE).setLevel(level)
    logging.getLogger(LOGGER_BOT).setLevel(level)
    logging.getLogger(LOGGER_MAIN).setLevel(level)

    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured",
        extra={
            "log_level": log_level,
            "log_format": log_format,
            "log_file": log_file,
            "console_output": console_output,
        },
    )


def get_log_level_from_env() -> str:
    """
    Get log level from environment variable.

    Checks for LOG_LEVEL environment variable.
    Defaults to INFO if not set or invalid.

    Returns:
        Log level string
    """
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    if level not in valid_levels:
        return "INFO"

    return level


def get_log_format_from_env() -> str:
    """
    Get log format from environment variable.

    Checks for LOG_FORMAT environment variable.
    Defaults to 'text' for development, 'json' for production.

    Returns:
        Log format string ('json' or 'text')
    """
    log_format = os.getenv("LOG_FORMAT", "text").lower()

    if log_format not in ["json", "text"]:
        return "text"

    return log_format


# Convenience function for quick setup from environment
# Used by bot.py and core.py when run as main modules
def setup_logging_from_env() -> None:
    """
    Setup logging using environment variables.

    Reads LOG_LEVEL and LOG_FORMAT from environment.
    Default: INFO level, text format, console output only.
    """
    log_level = get_log_level_from_env()
    log_format = get_log_format_from_env()
    log_file = os.getenv("LOG_FILE")

    # In production (JSON format), default to INFO
    # In development (text format), default to DEBUG
    if log_format == "json" and log_level == "INFO":
        pass  # Keep INFO for production
    elif log_format == "text" and os.getenv("ENV", "development") == "development":
        log_level = "DEBUG"

    setup_logging(
        log_level=log_level,
        log_format=log_format,
        log_file=log_file,
        console_output=True,
    )


# Pre-configured loggers for easy import
# These will use the root logger's configuration
CoreLogger = logging.getLogger(LOGGER_CORE)
BotLogger = logging.getLogger(LOGGER_BOT)
MainLogger = logging.getLogger(LOGGER_MAIN)
