from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import DBAPIError, InterfaceError, OperationalError, SQLAlchemyError
from sqlalchemy.exc import TimeoutError as PoolTimeoutError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.logging import get_logger
from app.responses import AppError, InternalError, ServiceUnavailable, error

log = get_logger(__name__)


# What a database call can raise: SQLAlchemy errors, plus raw OS-level errors (asyncpg raises
# ConnectionRefusedError, socket timeouts, ... unwrapped when it cannot reach the server).
DB_ERRORS = (SQLAlchemyError, OSError)


def _is_connectivity_problem(exc: Exception) -> bool:
    if isinstance(exc, OSError | OperationalError | InterfaceError | PoolTimeoutError):
        return True
    return isinstance(exc, DBAPIError) and exc.connection_invalidated


def to_app_error(action: str, exc: Exception) -> AppError:
    """Logs a database failure and maps it to a safe client-facing error (no internals leak)."""
    log.error("database_error", action=action, error=type(exc).__name__, exc_info=exc)
    if _is_connectivity_problem(exc):
        return ServiceUnavailable("Database is temporarily unavailable", "DATABASE_UNAVAILABLE")
    return InternalError(f"Could not {action}", "DATABASE_ERROR")


async def db_failure(db: AsyncSession, action: str, exc: Exception) -> AppError:
    """Rolls the session back, then returns the AppError for the caller to raise."""
    try:
        await db.rollback()
    except SQLAlchemyError:
        log.warning("rollback_failed", action=action)
    return to_app_error(action, exc)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error(_: Request, exc: AppError):
        # 4xx are the client's doing; the request middleware already records the status.
        log.debug("app_error", status=exc.status_code, code=exc.code, message=exc.message)
        return error(exc.status_code, exc.code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError):
        details = [
            {
                "field": ".".join(str(p) for p in e["loc"][1:]) or str(e["loc"][0]),
                "message": e["msg"],
            }
            for e in exc.errors()
        ]
        log.info("validation_failed", errors=details)
        return error(422, "VALIDATION_ERROR", "Request validation failed", details)

    @app.exception_handler(StarletteHTTPException)
    async def http_error(_: Request, exc: StarletteHTTPException):
        return error(exc.status_code, f"HTTP_{exc.status_code}", str(exc.detail))

    @app.exception_handler(SQLAlchemyError)
    async def database_error(_: Request, exc: SQLAlchemyError):
        # Safety net for database errors that escape an endpoint's own handling.
        err = to_app_error("complete the request", exc)
        return error(err.status_code, err.code, err.message)

    @app.exception_handler(Exception)
    async def unhandled(_: Request, exc: Exception):
        log.error("unhandled_error", path=_.url.path, exc_info=exc)
        return error(500, "INTERNAL_ERROR", "Something went wrong")
