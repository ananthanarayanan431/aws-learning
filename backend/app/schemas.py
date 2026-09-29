from datetime import date, datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from app.models import TaskPriority, TaskStatus

T = TypeVar("T")


# ---- Response envelopes -------------------------------------------------
class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "OK"
    data: T | None = None
    meta: dict[str, Any] | None = None


class ErrorDetail(BaseModel):
    code: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error: ErrorDetail


# ---- Domain schemas -----------------------------------------------------
class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    color: str = Field(default="#6366f1", pattern=r"^#[0-9a-fA-F]{6}$")


class CategoryOut(ORMModel, CategoryIn):
    id: int


class TagIn(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class TagOut(ORMModel, TagIn):
    id: int


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    status: TaskStatus = TaskStatus.todo
    priority: TaskPriority = TaskPriority.medium
    due_date: date | None = None
    planned_date: date | None = None
    category_id: int | None = None
    parent_id: int | None = None
    tag_ids: list[int] = []


class TaskUpdate(BaseModel):
    """Partial update: only fields present in the request body are changed."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: date | None = None
    planned_date: date | None = None
    category_id: int | None = None
    tag_ids: list[int] | None = None


class TaskOut(ORMModel):
    id: int
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    due_date: date | None
    planned_date: date | None
    completed_at: datetime | None
    category: CategoryOut | None
    tags: list[TagOut]
    parent_id: int | None
    subtasks: list["TaskOut"]
    created_at: datetime
    updated_at: datetime


class HealthOut(BaseModel):
    status: str
    service: str


class CarryOverOut(BaseModel):
    moved: int
