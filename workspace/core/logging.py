"""core.logging — Rich-based structured logger for the pipeline."""

from __future__ import annotations

import logging

from rich.console import Console
from rich.logging import RichHandler

from core.config import LOG_LEVEL

_console = Console(stderr=True)

_HANDLER = RichHandler(
    console=_console,
    show_time=True,
    show_path=False,
    markup=True,
)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger with rich formatting."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.addHandler(_HANDLER)
        logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    return logger
