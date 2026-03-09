from sqlalchemy import (
    Column, Integer, String, Float, Date, Boolean,
    Text, ForeignKey, DateTime, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    income_sources = relationship("IncomeSource", back_populates="user", cascade="all, delete")
    plaid_items = relationship("PlaidItem", back_populates="user", cascade="all, delete")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete")
    budgets = relationship("Budget", back_populates="user", cascade="all, delete")
    bills = relationship("Bill", back_populates="user", cascade="all, delete")


class IncomeSource(Base):
    __tablename__ = "income_sources"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)       # e.g. "Uber", "Part-time job"
    hourly_rate = Column(Float, nullable=False)  # e.g. 22.50
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="income_sources")


class PlaidItem(Base):
    __tablename__ = "plaid_items"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    access_token = Column(String, nullable=False)
    item_id = Column(String, unique=True, nullable=False)
    institution_name = Column(String)
    institution_id = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="plaid_items")
    accounts = relationship("Account", back_populates="plaid_item", cascade="all, delete")


class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plaid_item_id = Column(Integer, ForeignKey("plaid_items.id"), nullable=False)
    account_id = Column(String, unique=True, nullable=False)
    name = Column(String)
    official_name = Column(String)
    type = Column(String)        # depository, credit, investment
    subtype = Column(String)     # checking, savings, credit card
    mask = Column(String)        # last 4 digits
    balance_current = Column(Float)
    balance_available = Column(Float)
    currency = Column(String, default="USD")
    last_synced = Column(DateTime(timezone=True))

    plaid_item = relationship("PlaidItem", back_populates="accounts")


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(String, nullable=False)
    transaction_id = Column(String, unique=True, nullable=False)
    name = Column(String)
    merchant_name = Column(String)
    amount = Column(Float)       # positive = spending, negative = income (Plaid convention)
    date = Column(Date, nullable=False)
    category = Column(String)    # normalized top-level category
    subcategory = Column(String)
    is_pending = Column(Boolean, default=False)
    raw = Column(Text)           # full JSON from Plaid
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="transactions")

    __table_args__ = (
        Index("ix_transactions_user_date", "user_id", "date"),
        Index("ix_transactions_user_category", "user_id", "category"),
    )


class Budget(Base):
    __tablename__ = "budgets"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category = Column(String, nullable=False)   # e.g. "groceries"
    monthly_limit = Column(Float, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="budgets")


class Bill(Base):
    __tablename__ = "bills"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)       # e.g. "Rent", "Phone"
    amount = Column(Float, nullable=False)
    due_day = Column(Integer, nullable=False)   # day of month (1-31)
    is_recurring = Column(Boolean, default=True)

    user = relationship("User", back_populates="bills")
