from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..schemas import ReportListItem, ReportOut

router = APIRouter(tags=["reports"])


def _month_start(year: int, month: int) -> datetime:
    return datetime(year, month, 1)


def _month_end_exclusive(year: int, month: int) -> datetime:
    if month == 12:
        return datetime(year + 1, 1, 1)
    return datetime(year, month + 1, 1)


def _prev_year_month(year: int, month: int) -> tuple[int, int]:
    if month == 1:
        return year - 1, 12
    return year, month - 1


def _month_has_transactions(db: Session, year: int, month: int) -> bool:
    start = _month_start(year, month)
    end = _month_end_exclusive(year, month)
    return (
        db.query(models.Transaction.id)
        .filter(
            models.Transaction.date >= start,
            models.Transaction.date < end,
        )
        .first()
        is not None
    )


def _sum_amount(db: Session, year: int, month: int, tx_type: str) -> int:
    q = (
        db.query(func.coalesce(func.sum(models.Transaction.amount), 0))
        .filter(models.Transaction.type == tx_type)
        .filter(
            models.Transaction.date >= _month_start(year, month),
            models.Transaction.date < _month_end_exclusive(year, month),
        )
    )
    v = q.scalar()
    return int(v or 0)


def _expense_totals_by_category(db: Session, year: int, month: int) -> dict[int, tuple[str, int]]:
    start = _month_start(year, month)
    end = _month_end_exclusive(year, month)
    rows = (
        db.query(
            models.Transaction.category_id,
            models.Category.name,
            func.sum(models.Transaction.amount),
        )
        .join(models.Category, models.Category.id == models.Transaction.category_id)
        .filter(
            models.Transaction.type == "expense",
            models.Transaction.date >= start,
            models.Transaction.date < end,
        )
        .group_by(models.Transaction.category_id, models.Category.name)
        .all()
    )
    out: dict[int, tuple[str, int]] = {}
    for category_id, name, total in rows:
        if category_id is None:
            continue
        out[int(category_id)] = (str(name), int(total or 0))
    return out


def _category_breakdown_list(
    cat_map: dict[int, tuple[str, int]],
    total_expense: int,
) -> list[dict]:
    result = []
    for cid in sorted(cat_map.keys()):
        name, amt = cat_map[cid]
        ratio = (amt / total_expense) if total_expense > 0 else 0.0
        result.append(
            {
                "category_id": cid,
                "category_name": name,
                "total_amount": amt,
                "ratio": round(ratio, 6),
            }
        )
    return result


def _diff_rate(current: int, previous: int) -> float:
    if previous == 0:
        return 0.0
    return round((current - previous) / previous, 6)


def _build_prev_month_diff(
    db: Session,
    year: int,
    month: int,
    cur_income: int,
    cur_expense: int,
    cur_cat: dict[int, tuple[str, int]],
) -> dict | None:
    py, pm = _prev_year_month(year, month)
    if not _month_has_transactions(db, py, pm):
        return None

    prev_income = _sum_amount(db, py, pm, "income")
    prev_expense = _sum_amount(db, py, pm, "expense")
    prev_cat = _expense_totals_by_category(db, py, pm)

    all_ids = set(cur_cat) | set(prev_cat)
    categories: list[dict] = []
    for cid in sorted(all_ids):
        cur_name, cur_amt = cur_cat.get(cid, ("", 0))
        prev_name, prev_amt = prev_cat.get(cid, ("", 0))
        name = cur_name or prev_name or ""
        diff_amount = cur_amt - prev_amt
        if prev_amt:
            diff_rate = round(diff_amount / prev_amt, 6)
        else:
            diff_rate = 0.0 if diff_amount == 0 else 1.0
        categories.append(
            {
                "category_id": cid,
                "category_name": name,
                "diff_amount": diff_amount,
                "diff_rate": diff_rate,
            }
        )

    return {
        "income_diff": cur_income - prev_income,
        "income_diff_rate": _diff_rate(cur_income, prev_income),
        "expense_diff": cur_expense - prev_expense,
        "expense_diff_rate": _diff_rate(cur_expense, prev_expense),
        "categories": categories,
    }


def fetch_report_by_month(db: Session, year: int, month: int) -> models.Report | None:
    return (
        db.query(models.Report)
        .filter(models.Report.year == year, models.Report.month == month)
        .first()
    )


def generate_and_save_report(db: Session, year: int, month: int) -> models.Report:
    total_income = _sum_amount(db, year, month, "income")
    total_expense = _sum_amount(db, year, month, "expense")
    balance = total_income - total_expense
    cat_map = _expense_totals_by_category(db, year, month)
    category_breakdown = _category_breakdown_list(cat_map, total_expense)
    prev_month_diff = _build_prev_month_diff(
        db, year, month, total_income, total_expense, cat_map
    )
    now = datetime.now(timezone.utc)

    row = fetch_report_by_month(db, year, month)
    if row:
        row.total_income = total_income
        row.total_expense = total_expense
        row.balance = balance
        row.category_breakdown = category_breakdown
        row.prev_month_diff = prev_month_diff
        row.generated_at = now
    else:
        row = models.Report(
            year=year,
            month=month,
            total_income=total_income,
            total_expense=total_expense,
            balance=balance,
            category_breakdown=category_breakdown,
            prev_month_diff=prev_month_diff,
            generated_at=now,
        )
        db.add(row)

    db.commit()
    db.refresh(row)
    return row


@router.get("/api/v1/reports", response_model=list[ReportListItem])
def list_reports(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    rows = (
        db.query(models.Report)
        .order_by(models.Report.year.desc(), models.Report.month.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [ReportListItem.model_validate(r) for r in rows]


@router.get("/api/v1/reports/{year}/{month}", response_model=ReportOut)
def read_report(
    year: int = Path(..., ge=2000, le=2100),
    month: int = Path(..., ge=1, le=12),
    db: Session = Depends(get_db),
):
    row = fetch_report_by_month(db, year, month)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="レポートが見つかりません")
    return ReportOut.model_validate(row)


@router.post(
    "/api/v1/reports/{year}/{month}/generate",
    response_model=ReportOut,
    status_code=status.HTTP_201_CREATED,
)
def generate_report_endpoint(
    year: int = Path(..., ge=2000, le=2100),
    month: int = Path(..., ge=1, le=12),
    db: Session = Depends(get_db),
):
    row = generate_and_save_report(db, year, month)
    return ReportOut.model_validate(row)
