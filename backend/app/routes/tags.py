from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.errors import DB_ERRORS, db_failure
from app.logging import get_logger
from app.models import Tag
from app.responses import Conflict, NotFound, success
from app.schemas import ErrorResponse, SuccessResponse, TagIn, TagOut

log = get_logger(__name__)
router = APIRouter(prefix="/tags", tags=["tags"])
ERRORS = {
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
    503: {"model": ErrorResponse},
}


@router.get("", response_model=SuccessResponse[list[TagOut]], responses=ERRORS)
async def list_tags(db: AsyncSession = Depends(get_db)):
    try:
        rows = (await db.scalars(select(Tag).order_by(Tag.name))).all()
    except DB_ERRORS as exc:
        raise await db_failure(db, "list tags", exc) from exc
    return success([TagOut.model_validate(r) for r in rows])


@router.post("", response_model=SuccessResponse[TagOut], status_code=201, responses=ERRORS)
async def create_tag(body: TagIn, db: AsyncSession = Depends(get_db)):
    tag = Tag(name=body.name)
    db.add(tag)
    try:
        await db.commit()
        await db.refresh(tag)
    except IntegrityError as exc:
        await db.rollback()
        log.warning("tag_conflict", name=body.name)
        raise Conflict(f"Tag '{body.name}' already exists") from exc
    except DB_ERRORS as exc:
        raise await db_failure(db, "create tag", exc) from exc
    log.info("tag_created", tag_id=tag.id, name=tag.name)
    return success(TagOut.model_validate(tag), "Tag created", status_code=201)


@router.delete("/{tag_id}", response_model=SuccessResponse[None], responses=ERRORS)
async def delete_tag(tag_id: int, db: AsyncSession = Depends(get_db)):
    try:
        tag = await db.get(Tag, tag_id)
        if not tag:
            raise NotFound("Tag")
        await db.delete(tag)
        await db.commit()
    except DB_ERRORS as exc:
        raise await db_failure(db, "delete tag", exc) from exc
    log.info("tag_deleted", tag_id=tag_id)
    return success(None, "Tag deleted")
