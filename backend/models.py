from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from .database import Base

#カテゴリマスタ
class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    type = Column(String, index=True)
    is_fixed = Column(Integer, index=True)
    sort_order = Column(Integer, index=True)

#支払い方法マスタ
class PaymentMethod(Base):
    __tablename__ = "payment_methods"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    sort_order = Column(Integer, index=True)

#収支トランザクション
class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, index=True)
    type = Column(String, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"))
    amount = Column(Integer, index=True)
    payment_method_id = Column(Integer, ForeignKey("payment_methods.id"))
    memo = Column(String, index=True)
    fixed_cost_id = Column(Integer, ForeignKey("fixed_costs.id"))
    created_at = Column(DateTime, index=True)
    updated_at = Column(DateTime, index=True)

#固定費設定
class FixedCost(Base):
    __tablename__ = "fixed_costs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"))
    amount = Column(Integer, index=True)
    day_of_month = Column(Integer, index=True)
    is_active = Column(Integer, index=True)
    updated_at = Column(DateTime, index=True)

#月次レポート
class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, index=True)
    month = Column(Integer, index=True)
    total_income = Column(Integer, index=True)
    total_expense = Column(Integer, index=True)
    balance = Column(Integer, index=True)
    category_breakdown = Column(JSON, index=True)
    prev_month_diff = Column(JSON, index=True)
    generated_at = Column(DateTime, index=True)