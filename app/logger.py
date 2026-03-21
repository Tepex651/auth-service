import logging.config
from pathlib import Path
from typing import Any

import structlog

from app.containers.enums import LogLevel


def setup_logging(
    log_level: LogLevel,
    *,
    is_json_logging: bool = True,
    # destination: exactly one must be True
    to_stdout: bool = True,
    to_file: bool = False,
    log_file_path: str | Path | None = None,
) -> None:
    """
    structlog + stdlib logging setup.

    Destination rule:
      - exactly one of (to_stdout, to_file) must be True
    """

    if (to_stdout and to_file) or (not to_stdout and not to_file):
        raise ValueError("Choose exactly one destination: to_stdout=True OR to_file=True.")

    if to_file and not log_file_path:
        raise ValueError("log_file_path is required when to_file=True.")

    if log_file_path is not None:
        log_file_path = Path(log_file_path)
        if log_file_path.parent and not log_file_path.parent.exists():
            log_file_path.parent.mkdir(parents=True, exist_ok=True)

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.CallsiteParameterAdder(
            {
                structlog.processors.CallsiteParameter.LINENO,
            },
        ),
        structlog.processors.UnicodeDecoder(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    structlog_only_processors = [
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter
        if is_json_logging
        else structlog.dev.ConsoleRenderer(pad_event=30)
    ]

    processors: list[Any] = shared_processors + structlog_only_processors

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatters = {
        "json_formatter": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(ensure_ascii=False),
            "foreign_pre_chain": shared_processors,
        },
        "plain_formatter": {"format": "%(message)s"},
    }

    handlers: dict[str, Any] = {}
    root_handlers: list[str] = []

    if to_stdout:
        handlers["console"] = {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "json_formatter" if is_json_logging else "plain_formatter",
        }
        root_handlers = ["console"]

    if to_file:
        handlers["file"] = {
            "class": "logging.FileHandler",
            "filename": str(log_file_path),
            "mode": "a",
            "encoding": "utf-8",
            "formatter": "json_formatter" if is_json_logging else "plain_formatter",
        }
        root_handlers = ["file"]

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": formatters,
        "handlers": handlers,
        "loggers": {
            "": {"handlers": root_handlers, "level": log_level},
            "httpx": {"handlers": root_handlers, "level": "CRITICAL"},
            "uvicorn": {"handlers": [], "level": "CRITICAL"},
            "uvicorn.error": {"handlers": root_handlers, "level": log_level},
        },
    }

    logging.config.dictConfig(logging_config)


logger = structlog.get_logger()
