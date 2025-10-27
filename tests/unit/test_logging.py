"""Unit tests for logging infrastructure.

Tests the logging module functionality including:
- Logger setup with console and file handlers
- Log level configuration
- Log format validation
- Default logger configuration
- Module-level convenience functions
"""

import logging
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

from gem_flux_mcp.logging import (
    setup_logger,
    get_logger,
    configure_default_logger,
    get_default_logger,
    debug,
    info,
    warning,
    error,
    critical,
    LOG_FORMAT,
    DATE_FORMAT,
)


class TestSetupLogger:
    """Test the setup_logger function."""

    def test_setup_logger_default_name(self):
        """Test logger is created with default name."""
        logger = setup_logger()
        assert logger.name == "gem_flux_mcp"
        assert isinstance(logger, logging.Logger)

    def test_setup_logger_custom_name(self):
        """Test logger is created with custom name."""
        logger = setup_logger(name="custom_logger")
        assert logger.name == "custom_logger"

    def test_setup_logger_info_level(self):
        """Test logger is configured with INFO level."""
        logger = setup_logger(level="INFO")
        assert logger.level == logging.INFO

    def test_setup_logger_debug_level(self):
        """Test logger is configured with DEBUG level."""
        logger = setup_logger(level="DEBUG")
        assert logger.level == logging.DEBUG

    def test_setup_logger_warning_level(self):
        """Test logger is configured with WARNING level."""
        logger = setup_logger(level="WARNING")
        assert logger.level == logging.WARNING

    def test_setup_logger_error_level(self):
        """Test logger is configured with ERROR level."""
        logger = setup_logger(level="ERROR")
        assert logger.level == logging.ERROR

    def test_setup_logger_critical_level(self):
        """Test logger is configured with CRITICAL level."""
        logger = setup_logger(level="CRITICAL")
        assert logger.level == logging.CRITICAL

    def test_setup_logger_lowercase_level(self):
        """Test logger accepts lowercase level strings."""
        logger = setup_logger(level="debug")
        assert logger.level == logging.DEBUG

    def test_setup_logger_console_handler_enabled(self):
        """Test console handler is added when console=True."""
        logger = setup_logger(console=True)
        handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(handlers) >= 1
        # Check that at least one handler outputs to stdout
        stdout_handlers = [h for h in handlers if h.stream == sys.stdout]
        assert len(stdout_handlers) >= 1

    def test_setup_logger_console_handler_disabled(self):
        """Test console handler is NOT added when console=False."""
        logger = setup_logger(console=False, name="test_no_console")
        # Should have no StreamHandler targeting stdout
        stdout_handlers = [h for h in logger.handlers
                          if isinstance(h, logging.StreamHandler) and h.stream == sys.stdout]
        assert len(stdout_handlers) == 0

    def test_setup_logger_file_handler(self, tmp_path):
        """Test file handler is added when log_file is specified."""
        log_file = tmp_path / "test.log"
        logger = setup_logger(log_file=log_file, name="test_file_logger")

        # Check FileHandler exists
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 1

        # Verify log file is created
        assert log_file.exists()

    def test_setup_logger_file_handler_creates_parent_dirs(self, tmp_path):
        """Test file handler creates parent directories if they don't exist."""
        log_file = tmp_path / "nested" / "dir" / "test.log"
        logger = setup_logger(log_file=log_file, name="test_nested_logger")

        # Verify parent directories were created
        assert log_file.parent.exists()
        assert log_file.exists()

    def test_setup_logger_no_file_handler_when_none(self):
        """Test no file handler is added when log_file is None."""
        logger = setup_logger(log_file=None, name="test_no_file")
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 0

    def test_setup_logger_formatter_applied(self):
        """Test formatter is applied to handlers."""
        logger = setup_logger(console=True, name="test_formatter")
        for handler in logger.handlers:
            assert handler.formatter is not None
            assert LOG_FORMAT in handler.formatter._fmt
            assert DATE_FORMAT in handler.formatter.datefmt

    def test_setup_logger_no_propagation(self):
        """Test logger does not propagate to root logger."""
        logger = setup_logger(name="test_no_propagate")
        assert logger.propagate is False

    def test_setup_logger_clears_existing_handlers(self):
        """Test setup_logger clears existing handlers on reconfiguration."""
        # First setup
        logger = setup_logger(console=True, name="test_clear_handlers")
        initial_handler_count = len(logger.handlers)

        # Second setup (should clear and recreate)
        logger = setup_logger(console=True, name="test_clear_handlers")
        assert len(logger.handlers) == initial_handler_count

    def test_setup_logger_writes_to_file(self, tmp_path):
        """Test logger actually writes messages to log file."""
        log_file = tmp_path / "test_write.log"
        logger = setup_logger(level="INFO", log_file=log_file, console=False, name="test_write")

        # Write test message
        test_message = "Test log message"
        logger.info(test_message)

        # Verify message was written to file
        log_content = log_file.read_text()
        assert test_message in log_content
        assert "INFO" in log_content


class TestGetLogger:
    """Test the get_logger function."""

    def test_get_logger_returns_existing_logger(self):
        """Test get_logger returns an existing logger by name."""
        # Create a logger first
        original = setup_logger(name="test_get_logger")

        # Get the same logger
        retrieved = get_logger(name="test_get_logger")

        assert retrieved is original
        assert retrieved.name == "test_get_logger"

    def test_get_logger_default_name(self):
        """Test get_logger uses default name when not specified."""
        logger = get_logger()
        assert logger.name == "gem_flux_mcp"


class TestConfigureDefaultLogger:
    """Test the configure_default_logger function."""

    def test_configure_default_logger_returns_logger(self):
        """Test configure_default_logger returns a logger instance."""
        logger = configure_default_logger(level="INFO")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "gem_flux_mcp"

    def test_configure_default_logger_sets_level(self):
        """Test configure_default_logger sets the correct log level."""
        logger = configure_default_logger(level="DEBUG")
        assert logger.level == logging.DEBUG

    def test_configure_default_logger_with_file(self, tmp_path):
        """Test configure_default_logger with log file."""
        log_file = tmp_path / "default.log"
        logger = configure_default_logger(level="INFO", log_file=log_file)

        # Verify file handler exists
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 1
        assert log_file.exists()

    def test_configure_default_logger_can_be_reconfigured(self, tmp_path):
        """Test default logger can be reconfigured."""
        # First configuration
        log_file1 = tmp_path / "config1.log"
        logger1 = configure_default_logger(level="INFO", log_file=log_file1)

        # Second configuration (should replace)
        log_file2 = tmp_path / "config2.log"
        logger2 = configure_default_logger(level="DEBUG", log_file=log_file2)

        assert logger2.level == logging.DEBUG
        # Should have handlers for the new configuration
        assert any(isinstance(h, logging.FileHandler) for h in logger2.handlers)


class TestGetDefaultLogger:
    """Test the get_default_logger function."""

    def test_get_default_logger_returns_logger(self):
        """Test get_default_logger returns a logger instance."""
        logger = get_default_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "gem_flux_mcp"

    def test_get_default_logger_auto_configures(self):
        """Test get_default_logger auto-configures if not configured."""
        # Reset by configuring with a known state
        configure_default_logger(level="INFO")

        logger = get_default_logger()
        assert logger.level == logging.INFO

    def test_get_default_logger_consistent(self):
        """Test get_default_logger returns same instance on multiple calls."""
        logger1 = get_default_logger()
        logger2 = get_default_logger()
        assert logger1 is logger2

    def test_get_default_logger_auto_creates_if_none(self):
        """Test get_default_logger auto-creates logger if not configured yet."""
        # Force reset the default logger
        import gem_flux_mcp.logging as logging_module
        original_logger = logging_module._default_logger
        logging_module._default_logger = None

        # Should auto-create with INFO level
        logger = get_default_logger()
        assert logger is not None
        assert logger.name == "gem_flux_mcp"
        assert logger.level == logging.INFO

        # Restore original
        logging_module._default_logger = original_logger


class TestConvenienceFunctions:
    """Test module-level convenience logging functions."""

    def test_debug_function(self, tmp_path):
        """Test debug() convenience function writes DEBUG level message."""
        log_file = tmp_path / "debug.log"
        configure_default_logger(level="DEBUG", log_file=log_file, console=False)

        test_message = "Debug test message"
        debug(test_message)

        log_content = log_file.read_text()
        assert test_message in log_content
        assert "DEBUG" in log_content

    def test_info_function(self, tmp_path):
        """Test info() convenience function writes INFO level message."""
        log_file = tmp_path / "info.log"
        configure_default_logger(level="INFO", log_file=log_file, console=False)

        test_message = "Info test message"
        info(test_message)

        log_content = log_file.read_text()
        assert test_message in log_content
        assert "INFO" in log_content

    def test_warning_function(self, tmp_path):
        """Test warning() convenience function writes WARNING level message."""
        log_file = tmp_path / "warning.log"
        configure_default_logger(level="WARNING", log_file=log_file, console=False)

        test_message = "Warning test message"
        warning(test_message)

        log_content = log_file.read_text()
        assert test_message in log_content
        assert "WARNING" in log_content

    def test_error_function(self, tmp_path):
        """Test error() convenience function writes ERROR level message."""
        log_file = tmp_path / "error.log"
        configure_default_logger(level="ERROR", log_file=log_file, console=False)

        test_message = "Error test message"
        error(test_message)

        log_content = log_file.read_text()
        assert test_message in log_content
        assert "ERROR" in log_content

    def test_critical_function(self, tmp_path):
        """Test critical() convenience function writes CRITICAL level message."""
        log_file = tmp_path / "critical.log"
        configure_default_logger(level="CRITICAL", log_file=log_file, console=False)

        test_message = "Critical test message"
        critical(test_message)

        log_content = log_file.read_text()
        assert test_message in log_content
        assert "CRITICAL" in log_content

    def test_log_level_filtering(self, tmp_path):
        """Test log messages are filtered by configured level."""
        log_file = tmp_path / "filtering.log"
        configure_default_logger(level="WARNING", log_file=log_file, console=False)

        # These should NOT be logged (below WARNING)
        debug("Debug message - should not appear")
        info("Info message - should not appear")

        # These SHOULD be logged (WARNING and above)
        warning("Warning message - should appear")
        error("Error message - should appear")
        critical("Critical message - should appear")

        log_content = log_file.read_text()

        # Verify filtering
        assert "Debug message" not in log_content
        assert "Info message" not in log_content
        assert "Warning message" in log_content
        assert "Error message" in log_content
        assert "Critical message" in log_content


class TestLogFormatting:
    """Test log message formatting."""

    def test_log_format_includes_timestamp(self, tmp_path):
        """Test log messages include timestamp."""
        log_file = tmp_path / "format_timestamp.log"
        configure_default_logger(level="INFO", log_file=log_file, console=False)

        info("Test message")

        log_content = log_file.read_text()
        # Check for timestamp pattern: YYYY-MM-DD HH:MM:SS
        import re
        assert re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', log_content)

    def test_log_format_includes_level(self, tmp_path):
        """Test log messages include level name."""
        log_file = tmp_path / "format_level.log"
        configure_default_logger(level="DEBUG", log_file=log_file, console=False)

        debug("Debug message")
        info("Info message")
        warning("Warning message")

        log_content = log_file.read_text()
        assert "DEBUG" in log_content
        assert "INFO" in log_content
        assert "WARNING" in log_content

    def test_log_format_includes_logger_name(self, tmp_path):
        """Test log messages include logger name."""
        log_file = tmp_path / "format_name.log"
        logger = setup_logger(name="test_logger", level="INFO", log_file=log_file, console=False)

        logger.info("Test message")

        log_content = log_file.read_text()
        assert "test_logger" in log_content

    def test_log_format_includes_line_number(self, tmp_path):
        """Test log messages include line number."""
        log_file = tmp_path / "format_lineno.log"
        configure_default_logger(level="INFO", log_file=log_file, console=False)

        info("Test message")

        log_content = log_file.read_text()
        # Should contain ":NNN" pattern for line number
        import re
        assert re.search(r':\d+', log_content)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_setup_logger_with_empty_name(self):
        """Test logger with empty name defaults to root logger."""
        logger = setup_logger(name="")
        # Empty name creates root logger by Python logging convention
        assert logger.name == "root"

    def test_setup_logger_invalid_level_raises_error(self):
        """Test setup_logger raises error for invalid log level."""
        with pytest.raises(AttributeError):
            setup_logger(level="INVALID_LEVEL")

    def test_multiple_loggers_independent(self, tmp_path):
        """Test multiple loggers operate independently."""
        log_file1 = tmp_path / "logger1.log"
        log_file2 = tmp_path / "logger2.log"

        logger1 = setup_logger(name="logger1", level="DEBUG", log_file=log_file1, console=False)
        logger2 = setup_logger(name="logger2", level="ERROR", log_file=log_file2, console=False)

        # Logger1 should log DEBUG
        logger1.debug("Debug from logger1")
        # Logger2 should NOT log DEBUG (only ERROR+)
        logger2.debug("Debug from logger2")
        logger2.error("Error from logger2")

        log1_content = log_file1.read_text()
        log2_content = log_file2.read_text()

        assert "Debug from logger1" in log1_content
        assert "Debug from logger2" not in log2_content
        assert "Error from logger2" in log2_content

    def test_log_file_append_mode(self, tmp_path):
        """Test log file is opened in append mode."""
        log_file = tmp_path / "append.log"

        # First logger writes
        logger1 = setup_logger(name="append1", level="INFO", log_file=log_file, console=False)
        logger1.info("First message")

        # Second logger appends
        logger2 = setup_logger(name="append2", level="INFO", log_file=log_file, console=False)
        logger2.info("Second message")

        log_content = log_file.read_text()
        assert "First message" in log_content
        assert "Second message" in log_content

    def test_unicode_log_messages(self, tmp_path):
        """Test logging handles Unicode characters correctly."""
        log_file = tmp_path / "unicode.log"
        configure_default_logger(level="INFO", log_file=log_file, console=False)

        # Test various Unicode characters
        info("Test with emoji: 🧬🔬")
        info("Test with accents: café résumé")
        info("Test with symbols: α β γ δ")

        log_content = log_file.read_text()
        assert "🧬🔬" in log_content
        assert "café résumé" in log_content
        assert "α β γ δ" in log_content

    def test_log_with_format_args(self, tmp_path):
        """Test logging with format arguments."""
        log_file = tmp_path / "format_args.log"
        configure_default_logger(level="INFO", log_file=log_file, console=False)

        info("Test with args: %s %d", "string", 42)

        log_content = log_file.read_text()
        assert "Test with args: string 42" in log_content
