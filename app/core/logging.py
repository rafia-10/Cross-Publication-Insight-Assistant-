"""
app.core.logging
~~~~~~~~~~~~~~~~
Centralised logging configuration for the Cross-Publication Insight Assistant.

Usage
-----
    from app.core.logging import get_logger
    logger = get_logger(__name__)
    logger.info("Something happened", extra={"project_id": 42})

Environment Variables
---------------------
LOG_LEVEL   : DEBUG | INFO | WARNING | ERROR  (default: INFO)
LOG_FORMAT  : json | text                     (default: json)
"""

from __future__ import annotations

import logging
import sys
from typing import Optional

# Try to import python-json-logger; fall back to plain text if missing.
try:
    from pythonjsonlogger import json as jsonlogger  # type: ignore  # new API (>=3.x)
    _JSON_AVAILABLE = True
except ImportError:
    try:
        from pythonjsonlogger import jsonlogger  # type: ignore  # legacy API (2.x)
        _JSON_AVAILABLE = True
    except ImportError:
        _JSON_AVAILABLE = False

from app.config import settings

# --------------------------------------------------------------------------
# Correlation-ID context variable (set by the request middleware)
# --------------------------------------------------------------------------
import contextvars

correlation_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "correlation_id", default=None
)


# --------------------------------------------------------------------------
# Custom formatter that injects the correlation ID into every record
# --------------------------------------------------------------------------

class _CorrelationFilter(logging.Filter):
    """Attaches the current correlation_id to every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = correlation_id_var.get(None) or "-"
        return True


_TEXT_FMT = (
    "%(asctime)s [%(levelname)-8s] [%(correlation_id)s] %(name)s — %(message)s"
)


def _build_json_handler() -> logging.Handler:
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(correlation_id)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        rename_fields={"asctime": "timestamp", "levelname": "level", "name": "logger"},
    )
    handler.setFormatter(formatter)
    return handler


def _build_text_handler() -> logging.Handler:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(_TEXT_FMT, datefmt="%Y-%m-%dT%H:%M:%S")
    handler.setFormatter(formatter)
    return handler


def configure_logging() -> None:
    """
    Configure the root logger once at application start-up.
    Idempotent — safe to call multiple times.
    """
    root = logging.getLogger()

    # Avoid duplicate handlers if called more than once
    if getattr(root, "_insight_configured", False):
        return

    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root.setLevel(level)

    log_format = settings.log_format.lower()
    if log_format == "json" and _JSON_AVAILABLE:
        handler = _build_json_handler()
    else:
        handler = _build_text_handler()

    correlation_filter = _CorrelationFilter()
    handler.addFilter(correlation_filter)
    root.addHandler(handler)

    # Quieten noisy third-party libraries
    for noisy in ("httpx", "httpcore", "chromadb", "git", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    root._insight_configured = True  # type: ignore[attr-defined]


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger.  Call configure_logging() once before using loggers.
    Falls back gracefully if configure_logging() was never called.
    """
    return logging.getLogger(name)
