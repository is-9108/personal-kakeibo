"""初回起動時のマスタ投入（仕様書 2.3 カテゴリ定義・支払い方法）。"""

from __future__ import annotations

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


def ensure_master_data() -> None:
    """categories / payment_methods が1件も無いときだけ、仕様どおりの初期行を投入する。"""
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
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
