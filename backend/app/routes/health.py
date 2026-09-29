from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.responses import error, success
from app.schemas import ErrorResponse, HealthOut, SuccessResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=SuccessResponse[HealthOut])
def backend_health():
    return success(HealthOut(status="ok", service="backend").model_dump(), "Backend is healthy")


@router.get(
    "/db",
    response_model=SuccessResponse[HealthOut],
    responses={503: {"model": ErrorResponse}},
)
def database_health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        return error(503, "DATABASE_UNAVAILABLE", "Database is unreachable", str(exc.__class__.__name__))
    return success(HealthOut(status="ok", service="database").model_dump(), "Database is healthy")
