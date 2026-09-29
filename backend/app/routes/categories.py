from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.errors import DB_ERRORS, db_failure
from app.logging import get_logger
from app.models import Category
from app.responses import Conflict, NotFound, success
from app.schemas import CategoryIn, CategoryOut, ErrorResponse, SuccessResponse

log = get_logger(__name__)
router = APIRouter(prefix="/categories", tags=["categories"])
ERRORS = {
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
    503: {"model": ErrorResponse},
}


@router.get("", response_model=SuccessResponse[list[CategoryOut]], responses=ERRORS)
async def list_categories(db: AsyncSession = Depends(get_db)):
    try:
        rows = (await db.scalars(select(Category).order_by(Category.name))).all()
    except DB_ERRORS as exc:
        raise await db_failure(db, "list categories", exc) from exc
    return success([CategoryOut.model_validate(r) for r in rows])


@router.post("", response_model=SuccessResponse[CategoryOut], status_code=201, responses=ERRORS)
async def create_category(body: CategoryIn, db: AsyncSession = Depends(get_db)):
    cat = Category(**body.model_dump())
    db.add(cat)
    try:
        await db.commit()
        await db.refresh(cat)
    except IntegrityError as exc:
        await db.rollback()
        log.warning("category_conflict", name=body.name)
        raise Conflict(f"Category '{body.name}' already exists") from exc
    except DB_ERRORS as exc:
        raise await db_failure(db, "create category", exc) from exc
    log.info("category_created", category_id=cat.id, name=cat.name)
    return success(CategoryOut.model_validate(cat), "Category created", status_code=201)


@router.delete("/{category_id}", response_model=SuccessResponse[None], responses=ERRORS)
async def delete_category(category_id: int, db: AsyncSession = Depends(get_db)):
    try:
        cat = await db.get(Category, category_id)
        if not cat:
            raise NotFound("Category")
        await db.delete(cat)
        await db.commit()
    except DB_ERRORS as exc:
        raise await db_failure(db, "delete category", exc) from exc
    log.info("category_deleted", category_id=category_id)
    return success(None, "Category deleted")
