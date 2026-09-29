from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.errors import DB_ERRORS, db_failure
from app.logging import get_logger
from app.models import Category, Tag, Task, TaskPriority, TaskStatus
from app.responses import BadRequest, Conflict, NotFound, success
from app.schemas import ErrorResponse, SuccessResponse, TaskCreate, TaskOut, TaskUpdate

log = get_logger(__name__)
router = APIRouter(prefix="/tasks", tags=["tasks"])
ERRORS = {
    400: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
    503: {"model": ErrorResponse},
}


async def _load_tags(db: AsyncSession, tag_ids: list[int]) -> list[Tag]:
    ids = set(tag_ids)
    tags = list(await db.scalars(select(Tag).where(Tag.id.in_(ids)))) if ids else []
    if len(tags) != len(ids):
        log.warning("invalid_tag_ids", requested=sorted(ids), found=[t.id for t in tags])
        raise BadRequest("One or more tag_ids do not exist", "INVALID_TAG")
    return tags


async def _check_category(db: AsyncSession, category_id: int | None) -> None:
    if category_id is not None and not await db.get(Category, category_id):
        raise BadRequest("category_id does not exist", "INVALID_CATEGORY")


def _sync_completion(task: Task) -> None:
    if task.status == TaskStatus.done:
        task.completed_at = task.completed_at or datetime.now(UTC)
    else:
        task.completed_at = None


async def get_task_or_404(db: AsyncSession, task_id: int) -> Task:
    task = await db.get(Task, task_id)
    if not task:
        raise NotFound("Task")
    return task


@router.get("", response_model=SuccessResponse[list[TaskOut]])
async def list_tasks(
    db: AsyncSession = Depends(get_db),
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
        q = q.where(Task.title.icontains(search, autoescape=True))
    try:
        result = await db.scalars(q.order_by(Task.id.desc()).limit(limit).offset(offset))
        rows = result.unique().all()
    except DB_ERRORS as exc:
        raise await db_failure(db, "list tasks", exc) from exc
    return success(
        [TaskOut.model_validate(r) for r in rows],
        meta={"limit": limit, "offset": offset, "count": len(rows)},
    )


@router.post("", response_model=SuccessResponse[TaskOut], status_code=201, responses=ERRORS)
async def create_task(body: TaskCreate, db: AsyncSession = Depends(get_db)):
    try:
        await _check_category(db, body.category_id)
        if body.parent_id is not None:
            parent = await db.get(Task, body.parent_id)
            if not parent:
                raise BadRequest("parent_id does not exist", "INVALID_PARENT")
            if parent.parent_id is not None:
                log.warning("subtask_nesting_rejected", parent_id=body.parent_id)
                raise BadRequest("Subtasks cannot be nested more than one level", "INVALID_PARENT")
        task = Task(**body.model_dump(exclude={"tag_ids"}), tags=await _load_tags(db, body.tag_ids))
        _sync_completion(task)
        db.add(task)
        await db.commit()
        await db.refresh(task)
    except IntegrityError as exc:
        # A referenced category/tag/parent was deleted between the check and the insert.
        await db.rollback()
        log.warning("task_create_integrity_error", error=str(exc.orig))
        raise Conflict("A referenced category, tag or parent task no longer exists") from exc
    except DB_ERRORS as exc:
        raise await db_failure(db, "create task", exc) from exc
    log.info("task_created", task_id=task.id, parent_id=task.parent_id, status=task.status.value)
    return success(TaskOut.model_validate(task), "Task created", status_code=201)


@router.get("/{task_id}", response_model=SuccessResponse[TaskOut], responses=ERRORS)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    try:
        task = await get_task_or_404(db, task_id)
    except DB_ERRORS as exc:
        raise await db_failure(db, "fetch task", exc) from exc
    return success(TaskOut.model_validate(task))


@router.patch("/{task_id}", response_model=SuccessResponse[TaskOut], responses=ERRORS)
async def update_task(task_id: int, body: TaskUpdate, db: AsyncSession = Depends(get_db)):
    changes = body.model_dump(exclude_unset=True)
    if "title" in changes and changes["title"] is None:
        raise BadRequest("title cannot be null")
    try:
        task = await get_task_or_404(db, task_id)
        if "category_id" in changes:
            await _check_category(db, changes["category_id"])
        if "tag_ids" in changes:
            task.tags = await _load_tags(db, changes.pop("tag_ids") or [])
        for field, value in changes.items():
            setattr(task, field, value)
        _sync_completion(task)
        await db.commit()
        await db.refresh(task)
    except IntegrityError as exc:
        await db.rollback()
        log.warning("task_update_integrity_error", task_id=task_id, error=str(exc.orig))
        raise Conflict("A referenced category or tag no longer exists") from exc
    except DB_ERRORS as exc:
        raise await db_failure(db, "update task", exc) from exc
    log.info("task_updated", task_id=task.id, fields=sorted(changes))
    return success(TaskOut.model_validate(task), "Task updated")


@router.delete("/{task_id}", response_model=SuccessResponse[None], responses=ERRORS)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await db.delete(await get_task_or_404(db, task_id))
        await db.commit()
    except DB_ERRORS as exc:
        raise await db_failure(db, "delete task", exc) from exc
    log.info("task_deleted", task_id=task_id)
    return success(None, "Task deleted")
