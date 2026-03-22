from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db

router = APIRouter(tags=["categories"])


def get_categories(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Category).offset(skip).limit(limit).all()


@router.get("/api/v1/categories")
def read_categories(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    return get_categories(db, skip=skip, limit=limit)
