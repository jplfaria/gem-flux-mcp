"""Logging infrastructure for Gem-Flux MCP Server.

This module provides centralized logging configuration with console and file handlers.
Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
"""

import logging
import sys
from pathlib import Path
from typing import Optional


# Default log format with timestamp, level, module, and message
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(
    name: str = "gem_flux_mcp",
    level: str = "INFO",
    log_file: Optional[Path] = None,
    console: bool = True,
) -> logging.Logger:
    """Set up logger with console and/or file handlers.

    Args:
        name: Logger name (default: "gem_flux_mcp")
        level: Log level as string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional, no file logging if None)
        console: Enable console logging (default: True)

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logger("gem_flux_mcp", level="DEBUG", log_file=Path("server.log"))
        >>> logger.info("Server starting...")
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if log_file:
        # Ensure parent directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str = "gem_flux_mcp") -> logging.Logger:
    """Get existing logger by name.

    Args:
        name: Logger name (default: "gem_flux_mcp")

    Returns:
        Logger instance

    Example:
        >>> logger = get_logger("gem_flux_mcp.database")
        >>> logger.debug("Loading compounds...")
    """
    return logging.getLogger(name)


# Default logger instance (configured on first import)
_default_logger: Optional[logging.Logger] = None


def configure_default_logger(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    console: bool = True,
) -> logging.Logger:
    """Configure the default gem_flux_mcp logger.

    This should be called once at server startup to configure logging
    for the entire application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        console: Enable console logging (default: True)

    Returns:
        Configured default logger

    Example:
        >>> configure_default_logger(level="DEBUG", log_file=Path("./gem-flux.log"))
    """
    global _default_logger
    _default_logger = setup_logger("gem_flux_mcp", level=level, log_file=log_file, console=console)
    return _default_logger


def get_default_logger() -> logging.Logger:
    """Get the default gem_flux_mcp logger.

    If not yet configured, returns a basic logger with INFO level.

    Returns:
        Default logger instance
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = setup_logger("gem_flux_mcp", level="INFO", console=True)
    return _default_logger


# Module-level convenience functions
def debug(msg: str, *args, **kwargs):
    """Log debug message using default logger."""
    get_default_logger().debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs):
    """Log info message using default logger."""
    get_default_logger().info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs):
    """Log warning message using default logger."""
    get_default_logger().warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs):
    """Log error message using default logger."""
    get_default_logger().error(msg, *args, **kwargs)


def critical(msg: str, *args, **kwargs):
    """Log critical message using default logger."""
    get_default_logger().critical(msg, *args, **kwargs)
