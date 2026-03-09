from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from database import get_db
from models import User, Budget, Bill, IncomeSource
from routes.auth import get_current_user

router = APIRouter(prefix="/api", tags=["budget"])


# ---- Schemas ----

class BudgetIn(BaseModel):
    category: str
    monthly_limit: float

class BillIn(BaseModel):
    name: str
    amount: float
    due_day: int  # day of month, e.g. 28 for rent

class IncomeSourceIn(BaseModel):
    name: str         # e.g. "Uber", "Part-time at Walmart"
    hourly_rate: float
    is_primary: bool = False


# ---- Budget routes ----

@router.get("/budgets")
def get_budgets(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    budgets = db.query(Budget).filter(Budget.user_id == user.id).all()
    return {"budgets": [{"id": b.id, "category": b.category, "monthly_limit": b.monthly_limit} for b in budgets]}


@router.post("/budgets")
def set_budget(body: BudgetIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Upsert — if a budget for this category already exists, just update the limit
    existing = db.query(Budget).filter(Budget.user_id == user.id, Budget.category == body.category).first()
    if existing:
        existing.monthly_limit = body.monthly_limit
    else:
        db.add(Budget(user_id=user.id, category=body.category, monthly_limit=body.monthly_limit))
    db.commit()
    return {"ok": True}


@router.delete("/budgets/{budget_id}")
def delete_budget(budget_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    b = db.query(Budget).filter(Budget.id == budget_id, Budget.user_id == user.id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Budget not found")
    db.delete(b)
    db.commit()
    return {"ok": True}


# ---- Bills routes ----

@router.get("/bills")
def get_bills(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    bills = db.query(Bill).filter(Bill.user_id == user.id).all()
    return {"bills": [{"id": b.id, "name": b.name, "amount": b.amount, "due_day": b.due_day} for b in bills]}


@router.post("/bills")
def add_bill(body: BillIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.add(Bill(user_id=user.id, name=body.name, amount=body.amount, due_day=body.due_day))
    db.commit()
    return {"ok": True}


@router.delete("/bills/{bill_id}")
def delete_bill(bill_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    b = db.query(Bill).filter(Bill.id == bill_id, Bill.user_id == user.id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Bill not found")
    db.delete(b)
    db.commit()
    return {"ok": True}


# ---- Income sources routes ----

@router.get("/income-sources")
def get_income_sources(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    sources = db.query(IncomeSource).filter(IncomeSource.user_id == user.id).all()
    return {"income_sources": [
        {"id": s.id, "name": s.name, "hourly_rate": s.hourly_rate, "is_primary": s.is_primary}
        for s in sources
    ]}


@router.post("/income-sources")
def add_income_source(body: IncomeSourceIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.add(IncomeSource(user_id=user.id, name=body.name, hourly_rate=body.hourly_rate, is_primary=body.is_primary))
    db.commit()
    return {"ok": True}


@router.delete("/income-sources/{source_id}")
def delete_income_source(source_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = db.query(IncomeSource).filter(IncomeSource.id == source_id, IncomeSource.user_id == user.id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Income source not found")
    db.delete(s)
    db.commit()
    return {"ok": True}
