from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..schemas import Transaction

router = APIRouter(tags=["transactions"])


def get_transactions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Transaction).offset(skip).limit(limit).all()


def create_transaction_record(db: Session, payload: Transaction):
    db_transaction = models.Transaction(
        date=payload.date,
        type=payload.type,
        category_id=payload.category_id,
        amount=payload.amount,
        payment_method_id=payload.payment_method_id,
        memo=payload.memo,
        fixed_cost_id=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


def update_transaction_record(db: Session, transaction_id: int, payload: Transaction):
    db_transaction = (
        db.query(models.Transaction)
        .filter(models.Transaction.id == transaction_id)
        .first()
    )
    if db_transaction is None:
        return None
    db_transaction.date = payload.date
    db_transaction.type = payload.type
    db_transaction.category_id = payload.category_id
    db_transaction.amount = payload.amount
    db_transaction.payment_method_id = payload.payment_method_id
    db_transaction.memo = payload.memo
    db_transaction.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


def delete_transaction_record(db: Session, transaction_id: int):
    db_transaction = (
        db.query(models.Transaction)
        .filter(models.Transaction.id == transaction_id)
        .first()
    )
    if db_transaction is None:
        return None
    db.delete(db_transaction)
    db.commit()
    return db_transaction


@router.get("/api/v1/transactions")
def read_transactions(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    return get_transactions(db, skip=skip, limit=limit)


@router.post("/api/v1/transactions", status_code=status.HTTP_201_CREATED)
def post_transaction(
    db: Session = Depends(get_db),
    body: Transaction = Body(...),
):
    return create_transaction_record(db, body)


@router.put("/api/v1/transactions/{transaction_id}")
def put_transaction(
    transaction_id: int,
    body: Transaction,
    db: Session = Depends(get_db),
):
    row = update_transaction_record(db, transaction_id, body)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="取引が見つかりません")
    return row


@router.delete("/api/v1/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_transaction(transaction_id: int, db: Session = Depends(get_db)):
    row = delete_transaction_record(db, transaction_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="取引が見つかりません")
