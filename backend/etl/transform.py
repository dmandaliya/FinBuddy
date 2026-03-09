# ETL Pipeline 2 — TRANSFORM
# Validates, normalizes, and enriches raw Plaid transaction objects.
# Produces clean dicts ready to be loaded into PostgreSQL.

import json
from datetime import date, datetime
from typing import List, Optional


# Plaid's category hierarchy → our normalized top-level categories
CATEGORY_MAP = {
    "food and drink": "food",
    "restaurants": "food",
    "groceries": "groceries",
    "supermarkets and groceries": "groceries",
    "travel": "transport",
    "transportation": "transport",
    "taxi": "transport",
    "ride share": "transport",
    "gas stations": "transport",
    "shops": "shopping",
    "clothing and accessories": "shopping",
    "department stores": "shopping",
    "electronics": "shopping",
    "entertainment": "entertainment",
    "recreation": "entertainment",
    "gyms and fitness centers": "entertainment",
    "arts and entertainment": "entertainment",
    "healthcare": "healthcare",
    "medical": "healthcare",
    "pharmacies": "healthcare",
    "rent and utilities": "housing",
    "utilities": "housing",
    "mortgage": "housing",
    "transfer": "transfer",
    "payment": "payment",
    "payroll": "income",
    "deposit": "income",
    "interest": "income",
    "cash advance": "other",
    "service": "other",
    "fees and charges": "fees",
    "bank fees": "fees",
}


def normalize_category(raw_categories: Optional[list]) -> tuple[str, str]:
    """
    Map Plaid's category list to our normalized (category, subcategory).
    Returns ("other", "") if unknown.
    """
    if not raw_categories:
        return "other", ""

    top = raw_categories[0].lower() if raw_categories else ""
    sub = raw_categories[1].lower() if len(raw_categories) > 1 else ""

    # Try subcategory first (more specific), then top-level
    category = CATEGORY_MAP.get(sub) or CATEGORY_MAP.get(top) or "other"
    return category, sub


def parse_date(raw_date) -> date:
    if isinstance(raw_date, date):
        return raw_date
    return datetime.strptime(str(raw_date), "%Y-%m-%d").date()


def validate_transaction(tx: dict) -> bool:
    """
    Basic validation: must have transaction_id, amount, and date.
    """
    if not getattr(tx, "transaction_id", None):
        return False
    if getattr(tx, "amount", None) is None:
        return False
    if getattr(tx, "date", None) is None:
        return False
    return True


def transform_transaction(tx, user_id: int) -> Optional[dict]:
    """
    Transform a single Plaid transaction object into a clean dict
    ready for database insertion.
    Returns None if validation fails.
    """
    if not validate_transaction(tx):
        return None

    category, subcategory = normalize_category(getattr(tx, "category", None))

    # Prefer merchant_name over name when available
    merchant = getattr(tx, "merchant_name", None) or getattr(tx, "name", "Unknown")

    try:
        raw_json = json.dumps(tx.to_dict(), default=str)
    except Exception:
        raw_json = "{}"

    return {
        "user_id": user_id,
        "account_id": tx.account_id,
        "transaction_id": tx.transaction_id,
        "name": getattr(tx, "name", "Unknown"),
        "merchant_name": merchant,
        "amount": float(tx.amount),
        "date": parse_date(tx.date),
        "category": category,
        "subcategory": subcategory,
        "is_pending": bool(getattr(tx, "pending", False)),
        "raw": raw_json,
    }


def transform_batch(transactions: list, user_id: int) -> List[dict]:
    """
    Transform a list of Plaid transaction objects.
    Skips invalid records and returns only clean dicts.
    """
    results = []
    skipped = 0
    for tx in transactions:
        cleaned = transform_transaction(tx, user_id)
        if cleaned:
            results.append(cleaned)
        else:
            skipped += 1

    if skipped:
        print(f"[Transform] Skipped {skipped} invalid transactions out of {len(transactions)}")

    return results
