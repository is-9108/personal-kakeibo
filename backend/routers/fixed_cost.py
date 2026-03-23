from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..schemas import FixedCost

router = APIRouter(tags=["fixed-costs"])


def get_fixed_costs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.FixedCost).offset(skip).limit(limit).all()


def update_fixed_cost_record(db: Session, fixed_cost_id: int, payload: FixedCost):
    db_fixed_cost = (
        db.query(models.FixedCost).filter(models.FixedCost.id == fixed_cost_id).first()
    )
    if db_fixed_cost:
        db_fixed_cost.amount = payload.amount
        db_fixed_cost.day_of_month = payload.day_of_month
        db_fixed_cost.is_active = 1 if payload.is_active else 0
        db.commit()
        db.refresh(db_fixed_cost)
    return db_fixed_cost


@router.get("/api/v1/fixed-costs")
def read_fixed_costs(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    return get_fixed_costs(db, skip=skip, limit=limit)


@router.put("/api/v1/fixed-costs/{fixed_cost_id}")
def put_fixed_cost(
    fixed_cost_id: int,
    payload: FixedCost,
    db: Session = Depends(get_db),
):
    return update_fixed_cost_record(db, fixed_cost_id, payload)
