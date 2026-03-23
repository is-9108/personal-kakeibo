from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db

router = APIRouter(tags=["categories"])


def get_categories(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    category_type: str | None = None,
):
    q = db.query(models.Category)
    if category_type is not None:
        q = q.filter(models.Category.type == category_type)
    return q.offset(skip).limit(limit).all()


@router.get("/api/v1/categories")
def read_categories(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    category_type: Annotated[
        Literal["income", "expense"] | None,
        Query(alias="type"),
    ] = None,
):
    return get_categories(db, skip=skip, limit=limit, category_type=category_type)
