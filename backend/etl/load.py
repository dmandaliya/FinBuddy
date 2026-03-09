# ETL Pipeline 3 — LOAD
# Upserts clean transaction dicts into PostgreSQL.
# Handles deduplication, account balance updates, and summary stats.

from datetime import datetime, timezone
from typing import List
from sqlalchemy.orm import Session

from models import Transaction, Account


def load_transactions(db: Session, clean_txs: List[dict]) -> dict:
    """
    Upsert a list of clean transaction dicts into the transactions table.
    Uses transaction_id as the unique key — skips duplicates.
    Returns a summary: { inserted, skipped, total }.
    """
    inserted = 0
    skipped = 0

    for tx in clean_txs:
        exists = (
            db.query(Transaction)
            .filter(Transaction.transaction_id == tx["transaction_id"])
            .first()
        )
        if exists:
            skipped += 1
            continue

        db.add(Transaction(**tx))
        inserted += 1

    db.commit()

    return {
        "inserted": inserted,
        "skipped": skipped,
        "total": len(clean_txs),
    }


def load_accounts(db: Session, plaid_accounts: list, user_id: int, plaid_item_id: int) -> int:
    """
    Upsert account records and update current balances.
    Returns count of accounts upserted.
    """
    count = 0
    now = datetime.now(timezone.utc)

    for acc in plaid_accounts:
        existing = (
            db.query(Account)
            .filter(Account.account_id == acc.account_id)
            .first()
        )

        balance_current = None
        balance_available = None
        if getattr(acc, "balances", None):
            balance_current = getattr(acc.balances, "current", None)
            balance_available = getattr(acc.balances, "available", None)

        if existing:
            existing.balance_current = balance_current
            existing.balance_available = balance_available
            existing.last_synced = now
        else:
            db.add(Account(
                user_id=user_id,
                plaid_item_id=plaid_item_id,
                account_id=acc.account_id,
                name=getattr(acc, "name", None),
                official_name=getattr(acc, "official_name", None),
                type=str(acc.type) if getattr(acc, "type", None) else None,
                subtype=str(acc.subtype) if getattr(acc, "subtype", None) else None,
                mask=getattr(acc, "mask", None),
                balance_current=balance_current,
                balance_available=balance_available,
                currency="USD",
                last_synced=now,
            ))
        count += 1

    db.commit()
    return count


def run_full_etl(db: Session, plaid_client, item, user_id: int, days_back: int = 90) -> dict:
    """
    Orchestrate the full ETL pipeline for a single PlaidItem:
      1. Ingest  — fetch from Plaid
      2. Transform — validate + normalize
      3. Load  — upsert to PostgreSQL
    Returns summary stats.
    """
    from etl.ingest import ingest_default_range, ingest_accounts
    from etl.transform import transform_batch

    # 1. Ingest
    raw_txs = ingest_default_range(plaid_client, item.access_token, days_back=days_back)
    raw_accounts = ingest_accounts(plaid_client, item.access_token)

    # 2. Transform
    clean_txs = transform_batch(raw_txs, user_id)

    # 3. Load
    tx_stats = load_transactions(db, clean_txs)
    acc_count = load_accounts(db, raw_accounts, user_id, item.id)

    return {
        "transactions": tx_stats,
        "accounts_synced": acc_count,
        "raw_fetched": len(raw_txs),
    }
