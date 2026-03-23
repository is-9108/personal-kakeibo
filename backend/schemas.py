from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class Transaction(BaseModel):
    date: datetime
    type: str
    category_id: int
    amount: int
    payment_method_id: int | None = None
    memo: str = ""

class FixedCost(BaseModel):
    amount: int
    day_of_month: int
    is_active: bool


class ReportListItem(BaseModel):
    year: int
    month: int
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportOut(BaseModel):
    id: int
    year: int
    month: int
    total_income: int
    total_expense: int
    balance: int
    category_breakdown: list[dict[str, Any]]
    prev_month_diff: dict[str, Any] | None
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)