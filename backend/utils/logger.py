"""
Production logging configuration.
Structured log format with request context, rotated file output.
"""

import logging
import os
import sys
from datetime import datetime


def setup_logger(name: str = "app", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(level)

    # ── Format: timestamp | level | module | message ──
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)-20s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler — force UTF-8 to avoid Windows cp1252 encoding errors
    console = logging.StreamHandler(
        open(sys.stdout.fileno(), mode="w", encoding="utf-8", closefd=False)
    )
    console.setLevel(level)
    console.setFormatter(fmt)
    logger.addHandler(console)

    # File handler — always UTF-8
    try:
        os.makedirs("logs", exist_ok=True)
        file_handler = logging.FileHandler(
            f"logs/app_{datetime.now():%Y%m%d}.log", mode="a", encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)
    except Exception:
        pass  # Don't crash if log dir is not writable

    return logger


# Pre-configured loggers for each module
log = setup_logger("app")