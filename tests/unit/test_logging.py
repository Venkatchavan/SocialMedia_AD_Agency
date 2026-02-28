"""Tests for structured logging (U-11)."""

from __future__ import annotations

import logging

from app.core.logging import get_logger, setup_logging


class TestSetupLogging:
    """setup_logging() configures structlog correctly."""

    def test_dev_mode_configures(self) -> None:
        setup_logging(env="dev")
        logger = get_logger("test")
        assert logger is not None

    def test_prod_mode_configures(self) -> None:
        setup_logging(env="prod")
        logger = get_logger("test")
        assert logger is not None

    def test_get_logger_returns_bound_logger(self) -> None:
        setup_logging(env="dev")
        logger = get_logger("my_module")
        assert hasattr(logger, "info")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")

    def test_root_logger_has_handler(self) -> None:
        setup_logging(env="dev")
        root = logging.getLogger()
        assert len(root.handlers) >= 1

    def test_noisy_loggers_quieted(self) -> None:
        setup_logging(env="prod")
        assert logging.getLogger("uvicorn.access").level >= logging.WARNING
        assert logging.getLogger("sqlalchemy.engine").level >= logging.WARNING
