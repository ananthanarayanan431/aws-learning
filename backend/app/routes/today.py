from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Task, TaskStatus
from app.responses import success
from app.schemas import CarryOverOut, SuccessResponse, TaskOut

router = APIRouter(prefix="/today", tags=["today"])


def _overdue_planned(today: date):
    return (
        Task.parent_id.is_(None),
        Task.status != TaskStatus.done,
        Task.planned_date < today,
    )


@router.get("", response_model=SuccessResponse[list[TaskOut]])
def today_view(db: Session = Depends(get_db)):
    """Tasks planned for today, plus unfinished ones planned for earlier days."""
    today = date.today()
    q = select(Task).where(
        Task.parent_id.is_(None),
        (Task.planned_date == today)
        | ((Task.planned_date < today) & (Task.status != TaskStatus.done)),
    )
    rows = db.scalars(q.order_by(Task.planned_date, Task.id)).unique().all()
    return success(
        [TaskOut.model_validate(r) for r in rows],
        meta={"date": today.isoformat(), "count": len(rows)},
    )


@router.post("/carry-over", response_model=SuccessResponse[CarryOverOut])
def carry_over(db: Session = Depends(get_db)):
    """Moves every unfinished task planned before today to today."""
    today = date.today()
    result = db.execute(update(Task).where(*_overdue_planned(today)).values(planned_date=today))
    db.commit()
    moved = result.rowcount
    return success(CarryOverOut(moved=moved), f"Carried over {moved} task(s) to today")
