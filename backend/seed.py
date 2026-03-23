"""初回起動時のマスタ投入（仕様書 2.3・固定費初期値）。"""

from __future__ import annotations

from datetime import datetime, timezone

from . import models
from .database import SessionLocal

# (name, type, is_fixed, sort_order) — type は income / expense、is_fixed は 0/1
_CATEGORY_SEED: list[tuple[str, str, int, int]] = [
    ("給与", "income", 0, 1),
    ("その他収入", "income", 0, 2),
    ("食費", "expense", 0, 1),
    ("外食", "expense", 0, 2),
    ("日用品", "expense", 0, 3),
    ("交通費", "expense", 0, 4),
    ("家賃", "expense", 1, 5),
    ("光熱費", "expense", 0, 6),
    ("サブスク", "expense", 0, 7),
    ("NISA", "expense", 1, 8),
    ("その他", "expense", 0, 9),
]

_PAYMENT_METHOD_SEED: list[tuple[str, int]] = [
    ("楽天Pay", 1),
    ("クレジットカード", 2),
    ("現金", 3),
]

# (固定費名, 紐づけるカテゴリ名, 金額, 毎月の日, 有効1/無効0) — カテゴリ名で categories を引く
_FIXED_COST_SEED: list[tuple[str, str, int, int, int]] = [
    ("家賃", "家賃", 87220, 25, 1),
    ("NISA", "NISA", 10000, 16, 1),
]


def ensure_master_data() -> None:
    """マスタ・固定費が空のときだけ初期行を投入する。"""
    db = SessionLocal()
    try:
        if db.query(models.Category).first() is None:
            for name, typ, is_fixed, sort_order in _CATEGORY_SEED:
                db.add(
                    models.Category(
                        name=name,
                        type=typ,
                        is_fixed=is_fixed,
                        sort_order=sort_order,
                    )
                )
            db.commit()

        if db.query(models.PaymentMethod).first() is None:
            for name, sort_order in _PAYMENT_METHOD_SEED:
                db.add(
                    models.PaymentMethod(
                        name=name,
                        sort_order=sort_order,
                    )
                )
            db.commit()

        if db.query(models.FixedCost).first() is None:
            now = datetime.now(timezone.utc)
            for fc_name, category_name, amount, day_of_month, is_active in _FIXED_COST_SEED:
                cat = (
                    db.query(models.Category)
                    .filter(models.Category.name == category_name)
                    .first()
                )
                if cat is None:
                    continue
                db.add(
                    models.FixedCost(
                        name=fc_name,
                        category_id=cat.id,
                        amount=amount,
                        day_of_month=day_of_month,
                        is_active=is_active,
                        updated_at=now,
                    )
                )
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
