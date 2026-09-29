from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Category
from app.responses import Conflict, NotFound, success
from app.schemas import CategoryIn, CategoryOut, ErrorResponse, SuccessResponse

router = APIRouter(prefix="/categories", tags=["categories"])
ERRORS = {404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}}


@router.get("", response_model=SuccessResponse[list[CategoryOut]])
def list_categories(db: Session = Depends(get_db)):
    rows = db.scalars(select(Category).order_by(Category.name)).all()
    return success([CategoryOut.model_validate(r) for r in rows])


@router.post("", response_model=SuccessResponse[CategoryOut], status_code=201, responses=ERRORS)
def create_category(body: CategoryIn, db: Session = Depends(get_db)):
    cat = Category(**body.model_dump())
    db.add(cat)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise Conflict(f"Category '{body.name}' already exists")
    return success(CategoryOut.model_validate(cat), "Category created", status_code=201)


@router.delete("/{category_id}", response_model=SuccessResponse[None], responses=ERRORS)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    cat = db.get(Category, category_id)
    if not cat:
        raise NotFound("Category")
    db.delete(cat)
    db.commit()
    return success(None, "Category deleted")
