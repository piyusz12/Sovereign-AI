"""
Sovereign AI Workbench — Logging Configuration

Structured logging that works on Windows (no emoji in log format).
Each subsystem gets its own named logger.

Usage:
    from backend.logging_config import setup_logging
    setup_logging()
"""

from __future__ import annotations

import logging
import sys


LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s"
)

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: str = "INFO") -> None:
    """
    Configure logging for the entire application.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR)
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Force UTF-8 on stdout/stderr to avoid Windows encoding issues
    handler = logging.StreamHandler(
        stream=open(sys.stdout.fileno(), mode="w", encoding="utf-8", closefd=False)
    )
    handler.setLevel(numeric_level)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove any existing handlers to avoid duplicates
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Quiet down noisy third-party loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("hpack").setLevel(logging.WARNING)

    logging.getLogger("sovereign").info(
        "Logging initialized — level=%s", level.upper()
    )
