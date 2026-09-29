from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Category
from app.responses import Conflict, NotFound, success
from app.schemas import CategoryIn, CategoryOut, ErrorResponse, SuccessResponse

router = APIRouter(prefix="/categories", tags=["categories"])
ERRORS = {
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
}


@router.get("", response_model=SuccessResponse[list[CategoryOut]])
async def list_categories(db: AsyncSession = Depends(get_db)):
    rows = await db.scalars(select(Category).order_by(Category.name)).all()
    return success([CategoryOut.model_validate(r) for r in rows])


@router.post("", response_model=SuccessResponse[CategoryOut], status_code=201, responses=ERRORS)
async def create_category(body: CategoryIn, db: AsyncSession = Depends(get_db)):
    cat = Category(**body.model_dump())
    db.add(cat)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise Conflict(f"Category '{body.name}' already exists") from None
    await db.refresh(cat)
    return success(CategoryOut.model_validate(cat), "Category created", status_code=201)


@router.delete("/{category_id}", response_model=SuccessResponse[None], responses=ERRORS)
async def delete_category(category_id: int, db: AsyncSession = Depends(get_db)):
    cat = await db.get(Category, category_id)
    if not cat:
        raise NotFound("Category")
    await db.delete(cat)
    await db.commit()
    return success(None, "Category deleted")
