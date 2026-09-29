from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.errors import db_failure
from app.logging import get_logger
from app.models import Task, TaskStatus
from app.responses import success
from app.schemas import CarryOverOut, ErrorResponse, SuccessResponse, TaskOut

log = get_logger(__name__)
router = APIRouter(prefix="/today", tags=["today"])
ERRORS = {500: {"model": ErrorResponse}, 503: {"model": ErrorResponse}}


def _overdue_planned(today: date):
    return (
        Task.parent_id.is_(None),
        Task.status != TaskStatus.done,
        Task.planned_date < today,
    )


@router.get("", response_model=SuccessResponse[list[TaskOut]], responses=ERRORS)
async def today_view(db: AsyncSession = Depends(get_db)):
    """Tasks planned for today, plus unfinished ones planned for earlier days."""
    today = date.today()
    q = select(Task).where(
        Task.parent_id.is_(None),
        (Task.planned_date == today)
        | ((Task.planned_date < today) & (Task.status != TaskStatus.done)),
    )
    try:
        result = await db.scalars(q.order_by(Task.planned_date, Task.id))
        rows = result.unique().all()
    except SQLAlchemyError as exc:
        raise await db_failure(db, "load today view", exc) from exc
    return success(
        [TaskOut.model_validate(r) for r in rows],
        meta={"date": today.isoformat(), "count": len(rows)},
    )


@router.post("/carry-over", response_model=SuccessResponse[CarryOverOut], responses=ERRORS)
async def carry_over(db: AsyncSession = Depends(get_db)):
    """Moves every unfinished task planned before today to today."""
    today = date.today()
    try:
        result = await db.execute(
            update(Task).where(*_overdue_planned(today)).values(planned_date=today)
        )
        await db.commit()
    except SQLAlchemyError as exc:
        raise await db_failure(db, "carry over tasks", exc) from exc
    moved = result.rowcount
    log.info("carry_over", moved=moved, to=today.isoformat())
    return success(CarryOverOut(moved=moved), f"Carried over {moved} task(s) to today")
