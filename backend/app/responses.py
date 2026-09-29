from typing import Any

from fastapi.responses import JSONResponse

from app.schemas import ErrorDetail, ErrorResponse, SuccessResponse


class AppError(Exception):
    def __init__(self, status_code: int, code: str, message: str, details: Any = None):
        self.status_code, self.code, self.message, self.details = status_code, code, message, details


def NotFound(what: str) -> AppError:
    return AppError(404, "NOT_FOUND", f"{what} not found")


def BadRequest(message: str, code: str = "BAD_REQUEST") -> AppError:
    return AppError(400, code, message)


def Conflict(message: str) -> AppError:
    return AppError(409, "CONFLICT", message)


def success(data: Any = None, message: str = "OK", meta: dict | None = None, status_code: int = 200):
    body = SuccessResponse(data=data, message=message, meta=meta)
    return JSONResponse(status_code=status_code, content=body.model_dump(mode="json"))


def error(status_code: int, code: str, message: str, details: Any = None):
    body = ErrorResponse(message=message, error=ErrorDetail(code=code, details=details))
    return JSONResponse(status_code=status_code, content=body.model_dump(mode="json"))
