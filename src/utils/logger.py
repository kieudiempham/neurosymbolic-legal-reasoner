"""Thin logging facade (stdlib logging)."""

from __future__ import annotations

import logging
import sys
from typing import Any


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Return a configured logger (single handler to stderr)."""
    log = logging.getLogger(name)
    if log.handlers:
        return log
    log.setLevel(level)
    h = logging.StreamHandler(sys.stderr)
    h.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    log.addHandler(h)
    return log


def log_kv(logger: logging.Logger, message: str, **kwargs: Any) -> None:
    """Append key=value pairs to the log line for experiment traces."""
    extra = " ".join(f"{k}={v!r}" for k, v in kwargs.items())
    logger.info("%s %s", message, extra)
