from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models import User, Transaction, Budget
from routes.auth import get_current_user

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.get("")
def get_transactions(
    days: int = Query(default=30, ge=1, le=365),
    category: str = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Pull transactions for the last N days. Optional category filter.
    since = date.today() - timedelta(days=days)
    q = db.query(Transaction).filter(
        Transaction.user_id == user.id,
        Transaction.date >= since,
    )
    if category:
        q = q.filter(Transaction.category == category)

    txs = q.order_by(Transaction.date.desc()).all()

    return {"transactions": [
        {
            "id": t.id,
            "date": t.date.isoformat(),
            "name": t.name,
            "merchant_name": t.merchant_name,
            "amount": t.amount,
            "category": t.category,
            "subcategory": t.subcategory,
            "account_id": t.account_id,
            "is_pending": t.is_pending,
        }
        for t in txs
    ]}


@router.get("/summary")
def get_summary(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Summarize spending and income for the dashboard cards.
    # We keep it simple: sum positives as spending, negatives as income (Plaid style).
    since = date.today() - timedelta(days=days)
    txs = db.query(Transaction).filter(
        Transaction.user_id == user.id,
        Transaction.date >= since,
    ).all()

    total_spending = sum(t.amount for t in txs if t.amount > 0)
    total_income = sum(-t.amount for t in txs if t.amount < 0)

    # Group spending by our normalized categories
    by_category: dict = {}
    for t in txs:
        if t.amount > 0:
            cat = t.category or "other"
            by_category[cat] = by_category.get(cat, 0.0) + t.amount

    # Pull this month's budget limits so the frontend can show progress bars
    budgets = db.query(Budget).filter(Budget.user_id == user.id).all()
    budget_map = {b.category: b.monthly_limit for b in budgets}

    return {
        "total_spending": round(total_spending, 2),
        "total_income": round(total_income, 2),
        "net": round(total_income - total_spending, 2),
        "by_category": {k: round(v, 2) for k, v in by_category.items()},
        "budgets": budget_map,
        "days": days,
    }


@router.get("/recent")
def get_recent(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Just the latest N transactions — used on the dashboard preview table
    txs = (
        db.query(Transaction)
        .filter(Transaction.user_id == user.id)
        .order_by(Transaction.date.desc())
        .limit(limit)
        .all()
    )
    return {"transactions": [
        {
            "date": t.date.isoformat(),
            "name": t.name,
            "merchant_name": t.merchant_name,
            "amount": t.amount,
            "category": t.category,
        }
        for t in txs
    ]}
