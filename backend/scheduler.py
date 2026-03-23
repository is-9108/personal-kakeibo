"""APScheduler: 固定費の自動登録（毎日 09:00 JST で該当日照合）と月次レポート（毎月25日 09:00 JST・前月分）。"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from . import models
from .database import SQLALCHEMY_DATABASE_URL, SessionLocal
from .routers.reports import generate_and_save_report

logger = logging.getLogger(__name__)

JST = ZoneInfo("Asia/Tokyo")

# 既定はアプリ本体と同じ DB（kakeibo.db）。別ファイルにしたいときだけ APSCHEDULER_JOBSTORE_URL を設定。
JOBSTORE_URL = os.getenv("APSCHEDULER_JOBSTORE_URL", SQLALCHEMY_DATABASE_URL)


def _month_start(year: int, month: int) -> datetime:
    return datetime(year, month, 1)


def _month_end_exclusive(year: int, month: int) -> datetime:
    if month == 12:
        return datetime(year + 1, 1, 1)
    return datetime(year, month + 1, 1)


def _fixed_cost_txn_exists(db, fixed_cost_id: int, year: int, month: int) -> bool:
    start = _month_start(year, month)
    end = _month_end_exclusive(year, month)
    return (
        db.query(models.Transaction.id)
        .filter(
            models.Transaction.fixed_cost_id == fixed_cost_id,
            models.Transaction.date >= start,
            models.Transaction.date < end,
        )
        .first()
        is not None
    )


def run_apply_fixed_costs() -> None:
    """毎日 09:00 JST。当日が各固定費の登録日ならトランザクションを1件追加（同月・同一固定費はスキップ）。"""
    db = SessionLocal()
    try:
        today = datetime.now(JST).date()
        fixed_costs = (
            db.query(models.FixedCost).filter(models.FixedCost.is_active == 1).all()
        )
        for fc in fixed_costs:
            if fc.day_of_month != today.day:
                continue
            if _fixed_cost_txn_exists(db, fc.id, today.year, today.month):
                continue
            txn = models.Transaction(
                date=datetime(today.year, today.month, today.day, 9, 0, 0),
                type="expense",
                category_id=fc.category_id,
                amount=fc.amount,
                payment_method_id=None,
                memo=f"固定費: {fc.name}",
                fixed_cost_id=fc.id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(txn)
        db.commit()
    except Exception:
        logger.exception("固定費自動登録ジョブでエラー")
        db.rollback()
    finally:
        db.close()


def run_generate_prev_month_report() -> None:
    """毎月25日 09:00 JST。直前の暦月のレポートを生成・更新する。"""
    db = SessionLocal()
    try:
        now = datetime.now(JST)
        if now.month == 1:
            prev_year, prev_month = now.year - 1, 12
        else:
            prev_year, prev_month = now.year, now.month - 1
        generate_and_save_report(db, prev_year, prev_month)
    except Exception:
        logger.exception("月次レポート自動生成ジョブでエラー")
        db.rollback()
    finally:
        db.close()


def build_scheduler() -> BackgroundScheduler:
    jobstore_kwargs: dict = {}
    if JOBSTORE_URL.startswith("sqlite"):
        jobstore_kwargs["engine_options"] = {
            "connect_args": {"check_same_thread": False},
        }

    jobstores = {
        "default": SQLAlchemyJobStore(
            url=JOBSTORE_URL,
            **jobstore_kwargs,
        ),
    }

    scheduler = BackgroundScheduler(
        jobstores=jobstores,
        timezone=JST,
    )

    scheduler.add_job(
        run_apply_fixed_costs,
        CronTrigger(hour=9, minute=0),
        id="apply_fixed_costs_daily",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        run_generate_prev_month_report,
        CronTrigger(day=25, hour=9, minute=0),
        id="monthly_report_prev_month",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    return scheduler


_scheduler: BackgroundScheduler | None = None


def start_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        return _scheduler
    _scheduler = build_scheduler()
    _scheduler.start()
    logger.info("APScheduler を開始しました (jobstore=%s)", JOBSTORE_URL)
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        logger.info("APScheduler を停止しました")
        _scheduler = None
