import os
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from models import User, PlaidItem, Account
from routes.auth import get_current_user
from etl.load import run_full_etl

from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.sandbox_public_token_create_request import SandboxPublicTokenCreateRequest
from plaid import Configuration, ApiClient

router = APIRouter(prefix="/plaid", tags=["plaid"])

# --- Plaid client setup ---
PLAID_ENV = os.getenv("PLAID_ENV", "sandbox")
PLAID_HOSTS = {
    "sandbox": "https://sandbox.plaid.com",
    "development": "https://development.plaid.com",
    "production": "https://production.plaid.com",
}

_config = Configuration(host=PLAID_HOSTS.get(PLAID_ENV, "https://sandbox.plaid.com"))
_config.api_key["clientId"] = os.getenv("PLAID_CLIENT_ID")
_config.api_key["secret"] = os.getenv("PLAID_SECRET")
plaid_client = plaid_api.PlaidApi(ApiClient(_config))

PRODUCTS = [Products("transactions")]
COUNTRY_CODES = [CountryCode("US"), CountryCode("CA")]


# --- Schemas ---
class ExchangeRequest(BaseModel):
    public_token: str
    institution_name: str = "Unknown Bank"


# --- Routes ---
@router.post("/create_link_token")
def create_link_token(user: User = Depends(get_current_user)):
    try:
        req = LinkTokenCreateRequest(
            products=PRODUCTS,
            client_name="FinBuddy",
            country_codes=COUNTRY_CODES,
            language="en",
            user=LinkTokenCreateRequestUser(client_user_id=str(user.id)),
        )
        res = plaid_client.link_token_create(req)
        return {"link_token": res.link_token}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/exchange_public_token")
def exchange_public_token(
    body: ExchangeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        exchange_req = ItemPublicTokenExchangeRequest(public_token=body.public_token)
        exchange_res = plaid_client.item_public_token_exchange(exchange_req)
        access_token = exchange_res.access_token
        item_id = exchange_res.item_id
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    item = db.query(PlaidItem).filter(PlaidItem.item_id == item_id).first()
    if not item:
        item = PlaidItem(
            user_id=user.id,
            access_token=access_token,
            item_id=item_id,
            institution_name=body.institution_name,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
    else:
        item.access_token = access_token
        db.commit()

    stats = run_full_etl(db, plaid_client, item, user.id, days_back=90)
    return {"ok": True, "item_id": item_id, "etl": stats}


@router.post("/sandbox_connect")
def sandbox_connect(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """One-click sandbox bank connection for development/testing."""
    try:
        pub_req = SandboxPublicTokenCreateRequest(
            institution_id="ins_109508",
            initial_products=PRODUCTS,
        )
        pub_res = plaid_client.sandbox_public_token_create(pub_req)
        public_token = pub_res.public_token

        exchange_req = ItemPublicTokenExchangeRequest(public_token=public_token)
        exchange_res = plaid_client.item_public_token_exchange(exchange_req)
        access_token = exchange_res.access_token
        item_id = exchange_res.item_id
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    item = db.query(PlaidItem).filter(PlaidItem.item_id == item_id).first()
    if not item:
        item = PlaidItem(
            user_id=user.id,
            access_token=access_token,
            item_id=item_id,
            institution_name="First Platypus Bank (Sandbox)",
        )
        db.add(item)
        db.commit()
        db.refresh(item)

    stats = run_full_etl(db, plaid_client, item, user.id, days_back=90)
    return {"ok": True, "item_id": item_id, "etl": stats}


@router.get("/accounts")
def get_accounts(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    accounts = db.query(Account).filter(Account.user_id == user.id).all()
    return {"accounts": [
        {
            "id": a.id,
            "name": a.name,
            "official_name": a.official_name,
            "type": a.type,
            "subtype": a.subtype,
            "mask": a.mask,
            "balance_current": a.balance_current,
            "balance_available": a.balance_available,
            "last_synced": a.last_synced.isoformat() if a.last_synced else None,
        }
        for a in accounts
    ]}


@router.post("/sync")
def sync_all(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Re-run ETL for all linked bank accounts."""
    items = db.query(PlaidItem).filter(PlaidItem.user_id == user.id).all()
    if not items:
        raise HTTPException(status_code=400, detail="No banks linked yet")

    total_stats = {"transactions_inserted": 0, "accounts_synced": 0, "raw_fetched": 0}
    for item in items:
        stats = run_full_etl(db, plaid_client, item, user.id, days_back=90)
        total_stats["transactions_inserted"] += stats["transactions"]["inserted"]
        total_stats["accounts_synced"] += stats["accounts_synced"]
        total_stats["raw_fetched"] += stats["raw_fetched"]

    return {"ok": True, "stats": total_stats}
