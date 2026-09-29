from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.logging import get_logger
from app.responses import error, success
from app.schemas import ErrorResponse, HealthOut, SuccessResponse

log = get_logger(__name__)
router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=SuccessResponse[HealthOut])
async def backend_health():
    return success(HealthOut(status="ok", service="backend").model_dump(), "Backend is healthy")


@router.get(
    "/db",
    response_model=SuccessResponse[HealthOut],
    responses={503: {"model": ErrorResponse}},
)
async def database_health(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        log.error("database_unreachable", error=exc.__class__.__name__, exc_info=True)
        return error(
            503, "DATABASE_UNAVAILABLE", "Database is unreachable", str(exc.__class__.__name__)
        )
    return success(HealthOut(status="ok", service="database").model_dump(), "Database is healthy")
