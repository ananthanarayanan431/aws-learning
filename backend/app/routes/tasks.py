from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Category, Tag, Task, TaskPriority, TaskStatus
from app.responses import BadRequest, NotFound, success
from app.schemas import ErrorResponse, SuccessResponse, TaskCreate, TaskOut, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])
ERRORS = {
    400: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
}


def _load_tags(db: Session, tag_ids: list[int]) -> list[Tag]:
    ids = set(tag_ids)
    tags = list(db.scalars(select(Tag).where(Tag.id.in_(ids)))) if ids else []
    if len(tags) != len(ids):
        raise BadRequest("One or more tag_ids do not exist", "INVALID_TAG")
    return tags


def _check_category(db: Session, category_id: int | None) -> None:
    if category_id is not None and not db.get(Category, category_id):
        raise BadRequest("category_id does not exist", "INVALID_CATEGORY")


def _sync_completion(task: Task) -> None:
    if task.status == TaskStatus.done:
        task.completed_at = task.completed_at or datetime.now(timezone.utc)
    else:
        task.completed_at = None


def get_task_or_404(db: Session, task_id: int) -> Task:
    task = db.get(Task, task_id)
    if not task:
        raise NotFound("Task")
    return task


@router.get("", response_model=SuccessResponse[list[TaskOut]])
def list_tasks(
    db: Session = Depends(get_db),
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    category_id: int | None = None,
    tag_id: int | None = None,
    due_before: date | None = None,
    planned_date: date | None = None,
    search: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """Lists top-level tasks; subtasks are nested inside their parent."""
    q = select(Task).where(Task.parent_id.is_(None))
    if status:
        q = q.where(Task.status == status)
    if priority:
        q = q.where(Task.priority == priority)
    if category_id:
        q = q.where(Task.category_id == category_id)
    if tag_id:
        q = q.where(Task.tags.any(Tag.id == tag_id))
    if due_before:
        q = q.where(Task.due_date <= due_before)
    if planned_date:
        q = q.where(Task.planned_date == planned_date)
    if search:
        q = q.where(Task.title.ilike(f"%{search}%"))
    rows = db.scalars(q.order_by(Task.id.desc()).limit(limit).offset(offset)).unique().all()
    return success(
        [TaskOut.model_validate(r) for r in rows],
        meta={"limit": limit, "offset": offset, "count": len(rows)},
    )


@router.post("", response_model=SuccessResponse[TaskOut], status_code=201, responses=ERRORS)
def create_task(body: TaskCreate, db: Session = Depends(get_db)):
    _check_category(db, body.category_id)
    if body.parent_id is not None:
        parent = db.get(Task, body.parent_id)
        if not parent:
            raise BadRequest("parent_id does not exist", "INVALID_PARENT")
        if parent.parent_id is not None:
            raise BadRequest("Subtasks cannot be nested more than one level", "INVALID_PARENT")
    task = Task(**body.model_dump(exclude={"tag_ids"}), tags=_load_tags(db, body.tag_ids))
    _sync_completion(task)
    db.add(task)
    db.commit()
    return success(TaskOut.model_validate(task), "Task created", status_code=201)


@router.get("/{task_id}", response_model=SuccessResponse[TaskOut], responses=ERRORS)
def get_task(task_id: int, db: Session = Depends(get_db)):
    return success(TaskOut.model_validate(get_task_or_404(db, task_id)))


@router.patch("/{task_id}", response_model=SuccessResponse[TaskOut], responses=ERRORS)
def update_task(task_id: int, body: TaskUpdate, db: Session = Depends(get_db)):
    task = get_task_or_404(db, task_id)
    changes = body.model_dump(exclude_unset=True)
    if "title" in changes and changes["title"] is None:
        raise BadRequest("title cannot be null")
    if "category_id" in changes:
        _check_category(db, changes["category_id"])
    if "tag_ids" in changes:
        task.tags = _load_tags(db, changes.pop("tag_ids") or [])
    for field, value in changes.items():
        setattr(task, field, value)
    _sync_completion(task)
    db.commit()
    return success(TaskOut.model_validate(task), "Task updated")


@router.delete("/{task_id}", response_model=SuccessResponse[None], responses=ERRORS)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    db.delete(get_task_or_404(db, task_id))
    db.commit()
    return success(None, "Task deleted")
