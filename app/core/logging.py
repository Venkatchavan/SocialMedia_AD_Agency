"""Structured logging configuration — JSON output for production.

Configures structlog with:
- JSON rendering in prod
- Console rendering in dev
- Request/trace ID injection
- Timestamp and level injection
"""

from __future__ import annotations

import logging
import sys
import uuid

import structlog

from app.config import get_settings


def _add_trace_id(
    logger: structlog.types.WrappedLogger,
    method_name: str,
    event_dict: structlog.types.EventDict,
) -> structlog.types.EventDict:
    """Add a trace_id if not already present."""
    if "trace_id" not in event_dict:
        event_dict["trace_id"] = str(uuid.uuid4())[:8]
    return event_dict


def _add_app_info(
    logger: structlog.types.WrappedLogger,
    method_name: str,
    event_dict: structlog.types.EventDict,
) -> structlog.types.EventDict:
    """Add application metadata to every log entry."""
    event_dict.setdefault("service", "affiliate-ad-agency")
    return event_dict


def setup_logging(env: str | None = None) -> None:
    """Configure structlog and stdlib logging.

    Args:
        env: Environment name. If None, read from settings.
    """
    if env is None:
        env = get_settings().app_env

    is_prod = env in ("prod", "production", "staging")

    # Shared processors
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        _add_trace_id,
        _add_app_info,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if is_prod:
        # Production: JSON output, parseable by Datadog/Grafana/Loki
        renderer = structlog.processors.JSONRenderer()
    else:
        # Dev: colored console output
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging to use structlog formatter
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO if is_prod else logging.DEBUG)

    # Quiet noisy loggers
    for name in ("uvicorn.access", "sqlalchemy.engine", "httpx"):
        logging.getLogger(name).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a named structlog logger."""
    return structlog.get_logger(name)
