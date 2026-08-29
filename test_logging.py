"""
Unit tests for structured logging configuration.
"""

import json
import sys
import unittest
from io import StringIO
from unittest.mock import patch

import logging_config


class TestStructuredFormatter(unittest.TestCase):
    """Tests for StructuredFormatter class."""

    def setUp(self):
        self.formatter = logging_config.StructuredFormatter(
            include_timestamp=True, include_level=True, include_module=True
        )

    def test_format_produces_valid_json(self):
        """Formatter produces valid JSON output."""
        import logging

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = self.formatter.format(record)

        # Should be valid JSON
        parsed = json.loads(result)
        self.assertIsInstance(parsed, dict)

    def test_format_includes_message(self):
        """Formatted output includes the message."""
        import logging

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = self.formatter.format(record)
        parsed = json.loads(result)

        self.assertEqual(parsed["message"], "Test message")

    def test_format_includes_timestamp(self):
        """Formatted output includes ISO 8601 timestamp."""
        import logging

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )

        result = self.formatter.format(record)
        parsed = json.loads(result)

        self.assertIn("timestamp", parsed)
        # Should end with Z (UTC)
        self.assertTrue(parsed["timestamp"].endswith("Z"))

    def test_format_includes_level(self):
        """Formatted output includes log level."""
        import logging

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )

        result = self.formatter.format(record)
        parsed = json.loads(result)

        self.assertEqual(parsed["level"], "INFO")
        self.assertEqual(parsed["level_num"], logging.INFO)

    def test_format_includes_module(self):
        """Formatted output includes module information."""
        import logging

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test",
            args=(),
            exc_info=None,
        )
        record.module = "test_module"
        record.funcName = "test_function"

        result = self.formatter.format(record)
        parsed = json.loads(result)

        self.assertEqual(parsed["module"], "test_module")
        self.assertEqual(parsed["func"], "test_function")
        self.assertEqual(parsed["line"], 42)

    def test_format_includes_process_info(self):
        """Formatted output includes process information."""
        import logging
        import os

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )

        result = self.formatter.format(record)
        parsed = json.loads(result)

        self.assertIn("process", parsed)
        self.assertIn("id", parsed["process"])
        self.assertEqual(parsed["process"]["id"], os.getpid())

    def test_format_handles_exception(self):
        """Formatter handles exception info correctly."""
        import logging

        try:
            raise ValueError("Test error")
        except ValueError:
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        result = self.formatter.format(record)
        parsed = json.loads(result)

        self.assertIn("exception", parsed)
        self.assertEqual(parsed["exception"]["type"], "ValueError")
        self.assertEqual(parsed["exception"]["message"], "Test error")

    def test_format_handles_extra_fields(self):
        """Formatter includes extra fields from the record."""
        import logging

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )
        record.custom_field = "custom_value"
        record.another_field = 123

        result = self.formatter.format(record)
        parsed = json.loads(result)

        self.assertIn("extra", parsed)
        self.assertEqual(parsed["extra"]["custom_field"], "custom_value")
        self.assertEqual(parsed["extra"]["another_field"], 123)


class TestPlainTextFormatter(unittest.TestCase):
    """Tests for PlainTextFormatter class."""

    def setUp(self):
        self.formatter = logging_config.PlainTextFormatter()

    def test_format_produces_human_readable_output(self):
        """Formatter produces human-readable output."""
        import logging

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.module = "test_module"
        record.funcName = "test_function"

        result = self.formatter.format(record)

        # Should contain expected components
        self.assertIn("Test message", result)
        self.assertIn("INFO", result)
        self.assertIn("test_module", result)
        self.assertIn("test_function", result)
        self.assertIn("42", result)


class TestSetupLogging(unittest.TestCase):
    """Tests for setup_logging function."""

    def test_setup_logging_with_text_format(self):
        """Setup logging with text format works."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            logging_config.setup_logging(
                log_level="INFO", log_format="text", console_output=True
            )

            # Should have configured root logger
            import logging

            root_logger = logging.getLogger()
            self.assertEqual(root_logger.level, logging.INFO)

    def test_setup_logging_with_json_format(self):
        """Setup logging with JSON format works."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            logging_config.setup_logging(
                log_level="DEBUG", log_format="json", console_output=True
            )

            # Should have configured root logger
            import logging

            root_logger = logging.getLogger()
            self.assertEqual(root_logger.level, logging.DEBUG)

    def test_setup_logging_with_file_output(self):
        """Setup logging with file output works."""
        import os
        import tempfile
        import logging

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as f:
            temp_path = f.name

        try:
            logging_config.setup_logging(
                log_level="INFO",
                log_format="text",
                log_file=temp_path,
                console_output=False,
            )

            # Should have created file handler
            root_logger = logging.getLogger()
            file_handlers = [
                h for h in root_logger.handlers if isinstance(h, logging.FileHandler)
            ]
            self.assertGreater(len(file_handlers), 0)
        finally:
            # Close and remove file handlers to release file locks
            root_logger = logging.getLogger()
            for handler in root_logger.handlers[:]:
                if isinstance(handler, logging.FileHandler):
                    handler.close()
                    root_logger.removeHandler(handler)

            # Now it's safe to delete the file
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestGetLogger(unittest.TestCase):
    """Tests for get_logger function."""

    def test_get_logger_returns_logger(self):
        """get_logger returns a logger instance."""
        import logging

        logger = logging_config.get_logger("test.logger")
        self.assertIsInstance(logger, logging.Logger)

    def test_get_logger_with_level(self):
        """get_logger respects level parameter."""
        import logging

        logger = logging_config.get_logger("test.logger.level", level=logging.DEBUG)
        self.assertEqual(logger.level, logging.DEBUG)


class TestEnvironmentFunctions(unittest.TestCase):
    """Tests for environment-based configuration functions."""

    def test_get_log_level_from_env_default(self):
        """get_log_level_from_env returns INFO by default."""
        with patch.dict("os.environ", {}, clear=True):
            level = logging_config.get_log_level_from_env()
            self.assertEqual(level, "INFO")

    def test_get_log_level_from_env_valid(self):
        """get_log_level_from_env returns valid level."""
        with patch.dict("os.environ", {"LOG_LEVEL": "DEBUG"}, clear=True):
            level = logging_config.get_log_level_from_env()
            self.assertEqual(level, "DEBUG")

    def test_get_log_level_from_env_invalid(self):
        """get_log_level_from_env returns INFO for invalid level."""
        with patch.dict("os.environ", {"LOG_LEVEL": "INVALID"}, clear=True):
            level = logging_config.get_log_level_from_env()
            self.assertEqual(level, "INFO")

    def test_get_log_format_from_env_default(self):
        """get_log_format_from_env returns text by default."""
        with patch.dict("os.environ", {}, clear=True):
            log_format = logging_config.get_log_format_from_env()
            self.assertEqual(log_format, "text")

    def test_get_log_format_from_env_valid(self):
        """get_log_format_from_env returns valid format."""
        with patch.dict("os.environ", {"LOG_FORMAT": "json"}, clear=True):
            log_format = logging_config.get_log_format_from_env()
            self.assertEqual(log_format, "json")

    def test_get_log_format_from_env_invalid(self):
        """get_log_format_from_env returns text for invalid format."""
        with patch.dict("os.environ", {"LOG_FORMAT": "invalid"}, clear=True):
            log_format = logging_config.get_log_format_from_env()
            self.assertEqual(log_format, "text")


class TestLoggerConstants(unittest.TestCase):
    """Tests for logger name constants."""

    def test_logger_constants_defined(self):
        """Logger constants are defined."""
        self.assertEqual(logging_config.LOGGER_CORE, "dota_themer.core")
        self.assertEqual(logging_config.LOGGER_BOT, "dota_themer.bot")
        self.assertEqual(logging_config.LOGGER_MAIN, "dota_themer.main")

    def test_preconfigured_loggers_exist(self):
        """Pre-configured loggers exist."""
        import logging

        self.assertIsInstance(logging_config.CoreLogger, logging.Logger)
        self.assertIsInstance(logging_config.BotLogger, logging.Logger)
        self.assertIsInstance(logging_config.MainLogger, logging.Logger)


if __name__ == "__main__":
    unittest.main()
