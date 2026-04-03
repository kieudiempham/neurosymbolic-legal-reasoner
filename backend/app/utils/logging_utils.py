"""Structured logging setup."""

from __future__ import annotations

import logging
import sys
from typing import Any


def setup_logging(debug: bool = False) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stdout,
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_extra(logger: logging.Logger, msg: str, **fields: Any) -> None:
    parts = " ".join(f"{k}={v!r}" for k, v in fields.items())
    logger.info("%s | %s", msg, parts)
