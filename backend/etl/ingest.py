# ETL Pipeline 1 — INGEST
# Fetches raw transactions from Plaid API for all linked accounts.
# Handles pagination and returns raw transaction objects.

import time
from datetime import date, timedelta
from typing import List

from plaid.api import plaid_api
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.exceptions import ApiException


def ingest_transactions(
    client: plaid_api.PlaidApi,
    access_token: str,
    start_date: date,
    end_date: date,
    batch_size: int = 250,
) -> List[dict]:
    """
    Pull all transactions from Plaid for a given access_token and date range.
    Handles pagination automatically (offset-based).
    Returns a list of raw transaction dicts.
    """
    all_transactions = []
    offset = 0

    # Plaid sandbox sometimes returns PRODUCT_NOT_READY right after item creation.
    # We retry up to 5 times with a 3-second wait — usually resolves on the 2nd try.
    max_retries = 5
    retry_delay = 3

    while True:
        options = TransactionsGetRequestOptions(count=batch_size, offset=offset)
        req = TransactionsGetRequest(
            access_token=access_token,
            start_date=start_date,
            end_date=end_date,
            options=options,
        )

        for attempt in range(max_retries):
            try:
                resp = client.transactions_get(req)
                break
            except ApiException as e:
                if "PRODUCT_NOT_READY" in str(e) and attempt < max_retries - 1:
                    print(f"[Ingest] Product not ready, retrying in {retry_delay}s (attempt {attempt + 1})...")
                    time.sleep(retry_delay)
                else:
                    raise

        batch = resp.transactions
        all_transactions.extend(batch)

        if len(batch) < batch_size:
            break
        offset += len(batch)

    return all_transactions


def ingest_accounts(
    client: plaid_api.PlaidApi,
    access_token: str,
) -> List[dict]:
    """
    Pull account metadata and current balances from Plaid.
    Returns a list of account objects.
    """
    req = AccountsGetRequest(access_token=access_token)
    resp = client.accounts_get(req)
    return resp.accounts


def ingest_default_range(
    client: plaid_api.PlaidApi,
    access_token: str,
    days_back: int = 90,
) -> List[dict]:
    """
    Convenience wrapper: ingest the last N days of transactions.
    """
    end = date.today()
    start = end - timedelta(days=days_back)
    return ingest_transactions(client, access_token, start, end)
