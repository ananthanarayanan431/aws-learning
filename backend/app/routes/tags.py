from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tag
from app.responses import Conflict, NotFound, success
from app.schemas import ErrorResponse, SuccessResponse, TagIn, TagOut

router = APIRouter(prefix="/tags", tags=["tags"])
ERRORS = {404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}}


@router.get("", response_model=SuccessResponse[list[TagOut]])
def list_tags(db: Session = Depends(get_db)):
    rows = db.scalars(select(Tag).order_by(Tag.name)).all()
    return success([TagOut.model_validate(r) for r in rows])


@router.post("", response_model=SuccessResponse[TagOut], status_code=201, responses=ERRORS)
def create_tag(body: TagIn, db: Session = Depends(get_db)):
    tag = Tag(name=body.name)
    db.add(tag)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise Conflict(f"Tag '{body.name}' already exists")
    return success(TagOut.model_validate(tag), "Tag created", status_code=201)


@router.delete("/{tag_id}", response_model=SuccessResponse[None], responses=ERRORS)
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    tag = db.get(Tag, tag_id)
    if not tag:
        raise NotFound("Tag")
    db.delete(tag)
    db.commit()
    return success(None, "Tag deleted")
