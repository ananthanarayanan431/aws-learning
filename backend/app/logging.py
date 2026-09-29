"""Logging setup: structlog on top of stdlib logging.

Every record (ours, uvicorn's, SQLAlchemy's) goes through one pipeline, rendered as colored
console output in development and one JSON object per line in production.
"""

import logging
import sys

import structlog

from app.config import settings


def configure_logging() -> None:
    json_logs = settings.log_json if settings.log_json is not None else settings.is_production

    # Runs for records from both structlog and plain stdlib loggers.
    shared: list[structlog.typing.Processor] = [
        structlog.contextvars.merge_contextvars,  # request_id etc.
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso" if json_logs else "%H:%M:%S", utc=json_logs),
        structlog.processors.StackInfoRenderer(),
    ]
    renderer: structlog.typing.Processor = (
        structlog.processors.JSONRenderer()
        if json_logs
        else structlog.dev.ConsoleRenderer(colors=sys.stdout.isatty())
    )

    structlog.configure(
        processors=[*shared, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared,
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.processors.format_exc_info,
                renderer,
            ],
        )
    )
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(settings.log_level.upper())

    # Let uvicorn's loggers flow through our handler; the request middleware replaces its
    # access log (which has no request id or timing).
    for name in ("uvicorn", "uvicorn.error"):
        lg = logging.getLogger(name)
        lg.handlers, lg.propagate = [], True
    access = logging.getLogger("uvicorn.access")
    access.handlers, access.propagate = [], False

    # SQL echo is opt-in via LOG_LEVEL=DEBUG on sqlalchemy.engine; keep it quiet by default.
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.stdlib.get_logger(name)
