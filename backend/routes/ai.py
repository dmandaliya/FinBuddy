import os
import re
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import anthropic

from database import get_db
from models import User, Transaction, Budget, Bill, IncomeSource, Account
from routes.auth import get_current_user

router = APIRouter(prefix="/api/ai", tags=["ai"])

# We initialize the Anthropic client once at startup.
# The API key comes from the .env file.
claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-6"


# ---- Schema ----

class ChatRequest(BaseModel):
    message: str
    history: Optional[list] = []  # list of {"role": "user"/"assistant", "content": "..."}


# ---- Context builder ----

def build_financial_context(db: Session, user: User) -> str:
    """
    Build a compact but complete picture of the user's finances.
    This is injected into Claude's system prompt so every answer
    is grounded in real data — not generic advice.
    """
    today = date.today()
    month_start = today.replace(day=1)

    # Last 90 days of transactions
    txs_90 = db.query(Transaction).filter(
        Transaction.user_id == user.id,
        Transaction.date >= today - timedelta(days=90),
    ).all()

    # This month only
    txs_this_month = [t for t in txs_90 if t.date >= month_start]

    # Spending totals
    total_spent_month = sum(t.amount for t in txs_this_month if t.amount > 0)
    total_income_month = sum(-t.amount for t in txs_this_month if t.amount < 0)

    # Category breakdown this month
    by_cat: dict = {}
    for t in txs_this_month:
        if t.amount > 0:
            cat = t.category or "other"
            by_cat[cat] = by_cat.get(cat, 0.0) + t.amount
    top_cats = sorted(by_cat.items(), key=lambda x: x[1], reverse=True)[:8]
    cats_str = ", ".join(f"{c}: ${v:.0f}" for c, v in top_cats) if top_cats else "no data yet"

    # User's budgets
    budgets = db.query(Budget).filter(Budget.user_id == user.id).all()
    budget_lines = [f"{b.category}: ${b.monthly_limit:.0f}/month" for b in budgets]
    budgets_str = ", ".join(budget_lines) if budget_lines else "not set yet"

    # Bills — figure out what's due in next 30 days and total upcoming
    bills = db.query(Bill).filter(Bill.user_id == user.id).all()
    upcoming_bills_total = 0.0
    bill_lines = []
    for b in bills:
        due = today.replace(day=min(b.due_day, 28))
        if due < today:
            due = (due.replace(day=28) + timedelta(days=4)).replace(day=min(b.due_day, 28))
        days_away = (due - today).days
        if 0 <= days_away <= 30:
            upcoming_bills_total += b.amount
            bill_lines.append(f"{b.name} ${b.amount:.0f} due in {days_away} days")
    bills_str = "; ".join(bill_lines) if bill_lines else "none in next 30 days"

    # Account balances
    accounts = db.query(Account).filter(Account.user_id == user.id).all()
    total_balance = sum((a.balance_available or a.balance_current or 0) for a in accounts)
    acc_lines = [f"{a.name} ({a.subtype}): ${(a.balance_available or a.balance_current or 0):.0f}" for a in accounts]
    accounts_str = "; ".join(acc_lines) if acc_lines else "no accounts linked"

    # Net available after upcoming bills
    net_after_bills = max(0.0, total_balance - upcoming_bills_total)

    # Income sources with hourly rates — this powers the "hours of work" calculation
    income_sources = db.query(IncomeSource).filter(IncomeSource.user_id == user.id).all()
    income_str = ", ".join(
        f"{s.name} at ${s.hourly_rate:.2f}/hr" for s in income_sources
    ) if income_sources else "not set (user hasn't added income sources yet)"

    # Recent 10 transactions for context
    recent = sorted(txs_90, key=lambda t: t.date, reverse=True)[:10]
    recent_str = "; ".join(
        f"{t.date} {t.merchant_name or t.name} ${t.amount:.2f}" for t in recent
    ) if recent else "no recent transactions"

    return f"""
USER: {user.name}
TODAY: {today.isoformat()}

ACCOUNTS & BALANCES:
{accounts_str}
Total available balance: ${total_balance:.2f}
Net after upcoming bills: ${net_after_bills:.2f}

THIS MONTH ({month_start.strftime('%B %Y')}):
Income received: ${total_income_month:.2f}
Total spending: ${total_spent_month:.2f}
Spending by category: {cats_str}

MONTHLY BUDGETS:
{budgets_str}

UPCOMING BILLS (next 30 days):
{bills_str}
Total upcoming: ${upcoming_bills_total:.2f}

INCOME SOURCES (for hours-of-work calculations):
{income_str}

RECENT TRANSACTIONS:
{recent_str}
""".strip()


def hours_of_work_breakdown(amount: float, income_sources: list) -> str:
    """
    Translate a dollar amount into hours of work for each income source.
    This is what makes FinBuddy personal — not just 'you can't afford it'
    but 'that's 7 Uber hours'.
    """
    if not income_sources:
        return ""
    lines = []
    for s in income_sources:
        if s.hourly_rate > 0:
            hours = amount / s.hourly_rate
            lines.append(f"~{hours:.1f} hours of {s.name}")
    return " or ".join(lines) if lines else ""


# ---- Chat route ----

@router.post("/chat")
def chat(
    body: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Build the user's real financial context
    context = build_financial_context(db, user)

    # Income sources for hours-of-work feature
    income_sources = db.query(IncomeSource).filter(IncomeSource.user_id == user.id).all()

    # Check if the message is a "should I buy X for $Y" type question
    # so we can inject extra hours-of-work context into the system prompt
    hours_hint = ""
    amount_match = re.search(r"\$?\s*(\d+(?:\.\d{1,2})?)", body.message)
    if amount_match and any(w in body.message.lower() for w in ["buy", "afford", "purchase", "get", "spend"]):
        amount = float(amount_match.group(1))
        hours_hint = hours_of_work_breakdown(amount, income_sources)
        if hours_hint:
            hours_hint = f"\n\nFor reference: ${amount:.0f} equals {hours_hint}. Always mention this in your answer."

    system_prompt = f"""You are FinBuddy — a sharp, friendly personal finance assistant.
Use the user's real data below. Never give generic advice.

RESPONSE RULES (follow strictly):
- Be concise. Max 120 words. No long paragraphs.
- Always use this format for purchase questions:

**Verdict:** YES / WAIT / NO — one sentence reason.

**The numbers:**
- Balance after bills: $X
- After this purchase: $X
- Work hours cost: X hrs of [job] (only if income sources are set)

**Bottom line:** One practical sentence. If NO/WAIT, suggest one specific alternative.

For other questions (spending, budgets, trends): answer in 2-4 short bullet points with real numbers from their data.

Never use tables. Never write long paragraphs. Keep it scannable.
{hours_hint}

USER'S FINANCIAL SNAPSHOT:
{context}"""

    # Build message history for multi-turn conversation
    messages = []
    for msg in (body.history or [])[-10:]:  # keep last 10 exchanges max
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": body.message})

    try:
        response = claude.messages.create(
            model=MODEL,
            max_tokens=500,
            system=system_prompt,
            messages=messages,
        )
        reply = response.content[0].text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Claude API error: {str(e)}")

    return {"reply": reply}
