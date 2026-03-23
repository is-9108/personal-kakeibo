from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models
from ..database import get_db

router = APIRouter(tags=["payment-methods"])

def get_payment_methods(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.PaymentMethod).offset(skip).limit(limit).all()

@router.get("/api/v1/payment-methods")
def read_payment_methods(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    return get_payment_methods(db, skip=skip, limit=limit)
