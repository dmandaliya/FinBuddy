import streamlit as st
import requests
import pandas as pd
from datetime import date, datetime


# ================== CONFIG ==================
BACKEND_URL = "http://127.0.0.1:8001"
TIMEOUT = 12

HEALTH = f"{BACKEND_URL}/health"

_session = requests.Session()


# ================== API HELPERS ==================
class ApiError(Exception):
    pass


def _post_json(path: str, payload=None):
    url = f"{BACKEND_URL}{path}"
    try:
        r = _session.post(url, json=payload, timeout=TIMEOUT)
    except requests.RequestException as e:
        raise ApiError(f"Network error calling {path}: {e}") from e

    if r.status_code != 200:
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        raise ApiError(f"{path} failed ({r.status_code}): {detail}")

    try:
        return r.json()
    except Exception as e:
        raise ApiError(f"{path} returned non-JSON response") from e


def _get(path: str, params=None):
    url = f"{BACKEND_URL}{path}"
    try:
        r = _session.get(url, params=params, timeout=TIMEOUT)
    except requests.RequestException as e:
        raise ApiError(f"Network error calling {path}: {e}") from e

    if r.status_code != 200:
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        raise ApiError(f"{path} failed ({r.status_code}): {detail}")

    try:
        return r.json()
    except Exception as e:
        raise ApiError(f"{path} returned non-JSON response") from e


def create_link_token():
    return _post_json("/create_link_token")


def exchange_public_token(public_token: str):
    return _post_json("/exchange_public_token", {"public_token": public_token})


def fetch_transactions():
    # backend handles access_token from DB; no need to send it
    return _get("/api/transactions")


def sandbox_auto_connect():
    return _post_json("/plaid/sandbox_auto_connect")



def check_health():
    try:
        r = _session.get(HEALTH, timeout=5)
        if r.status_code == 200:
            return True, r.json()
        else:
            return False, r.text
    except Exception as e:
        return False, str(e)


# ================== STREAMLIT APP ==================
st.set_page_config(page_title="FinBuddy", layout="wide")

# ---- SESSION STATE ----
defaults = {
    "profile_name": "",
    "monthly_income": 0.0,
    "link_token": None,
    "sandbox_url": None,
    "public_token": None,
    "access_token": None,
    "item_id": None,
    "transactions": None,
    "active_section": "dashboard",  # dashboard | profile | bank | spending_budget
    "budget_groceries": 0.0,
    "budget_rent": 0.0,
    "budget_transport": 0.0,
    "budget_entertainment": 0.0,
    "budget_other": 0.0,
    "chat_history": [],
    "last_chat_msg": "",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ================== LAYOUT ==================
left_col, main_col, right_col = st.columns([1, 2, 1], gap="large")

# ---------- LEFT: PROFILE + NAV ----------
with left_col:
    st.markdown("### 👤 FinBuddy Profile")

    profile_name = st.session_state.profile_name or "Set up your profile"
    st.markdown(
        f"""
        <div style="border-radius: 12px; padding: 12px; border: 1px solid #444;">
            <div style="font-size: 32px;">🪙</div>
            <div style="font-weight: 600; margin-top: 4px;">{profile_name}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("View personal details"):
        st.session_state.active_section = "profile"

    st.markdown("### Pages")

    if st.button("🏠 Dashboard"):
        st.session_state.active_section = "dashboard"
    if st.button("🏦 Bank connect"):
        st.session_state.active_section = "bank"
    if st.button("📊 Spending & budget"):
        st.session_state.active_section = "spending_budget"

    healthy, _health_info = check_health()
    if healthy:
        st.success("Backend: online")
    else:
        st.error("Backend: offline")


# ---------- RIGHT: CHAT ----------


# ---------- RIGHT: CHAT ----------
with right_col:
    st.markdown("### 💬 Chat with FinBuddy")

    # 1) Show history (old messages)
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(
                f"<div style='background:#1f2933; padding:8px 10px; "
                f"border-radius:10px; margin-bottom:4px; text-align:right;'>{msg['text']}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<div style='background:#111827; padding:8px 10px; "
                f"border-radius:10px; margin-bottom:4px; border:1px solid #374151;'>{msg['text']}</div>",
                unsafe_allow_html=True,
            )

    # 2) Chat input (only ONE input, with a key)
    user_msg = st.text_input(
        "Ask something about your money or a purchase:",
        key="chat_input"
    )

    # 3) Helper functions stay the same
    def summarize_spending():
        txns = st.session_state.transactions or []
        total_spent = 0.0
        total_income = 0.0
        groceries_spent = 0.0
        for t in txns:
            amount = float(t.get("amount", 0))
            name = str(t.get("name", "")).lower()
            cat = str(t.get("category", "")).lower()
            if amount < 0:
                total_spent += -amount
                if "grocery" in name or "grocery" in cat:
                    groceries_spent += -amount
            else:
                total_income += amount
        return total_spent, groceries_spent, total_income

    def handle_chat(message: str) -> str:
        msg = message.lower()
        total_spent, groceries_spent, total_income = summarize_spending()

        total_budget = (
            st.session_state.budget_groceries
            + st.session_state.budget_rent
            + st.session_state.budget_transport
            + st.session_state.budget_entertainment
            + st.session_state.budget_other
        )

        if "grocery" in msg or "groceries" in msg:
            if st.session_state.budget_groceries > 0:
                return (
                    f"You planned **${st.session_state.budget_groceries:.2f}** for groceries.\n\n"
                    f"Based on your linked transactions, I see ~**${groceries_spent:.2f}** spent on groceries so far.\n"
                    f"You have about **${st.session_state.budget_groceries - groceries_spent:.2f}** left in your groceries budget."
                )
            else:
                return (
                    "I do not see a groceries budget set yet. Go to **Spending & budget** and set one, "
                    "then I can compare it to your actual spending."
                )

        if "can i buy" in msg or "afford" in msg or "buy" in msg:
            if st.session_state.monthly_income <= 0 or total_budget <= 0:
                return (
                    "To answer that properly, I need your monthly income and budgets.\n\n"
                    "Go to **Profile** to set your income and **Spending & budget** to set category budgets."
                )
            else:
                remain = st.session_state.monthly_income - total_spent
                return (
                    f"Rough check: Your monthly income is about **${st.session_state.monthly_income:.2f}**.\n"
                    f"I see total spending of about **${total_spent:.2f}**.\n"
                    f"You still have ~**${remain:.2f}** unspent this month (based on linked data).\n\n"
                    "So if this new purchase is important and does not break your category budgets, it looks okay. "
                    "If it is a large or non-essential purchase, you might want to wait or reduce spending in other areas."
                )

        if "summary" in msg or "overview" in msg or "spending" in msg:
            reply = "Here is a quick snapshot based on what I know:\n"
            reply += f"- Monthly income: **${st.session_state.monthly_income:.2f}**\n"
            reply += f"- Total planned budget: **${total_budget:.2f}**\n"
            reply += f"- Observed spending (from transactions): **${total_spent:.2f}**\n"
            if st.session_state.access_token:
                reply += "- Bank connection: **Linked** ✅\n"
            else:
                reply += "- Bank connection: **Not linked** ❌\n"
            return reply

        return (
            "I am FinBuddy, your money assistant.\n\n"
            "- Ask me about **groceries** to compare your groceries budget vs spending.\n"
            "- Ask **“can I buy …”** or **“can I afford …”** to get a rough check based on your income and spending.\n"
            "- Ask for a **summary** to see your income, budgets, and spending overview."
        )

    # 4) Handle new message safely (no infinite loop)
        # 4) Handle new message safely (no infinite loop)
    if user_msg:
        # Extra safety: only respond if different from last processed message
        if st.session_state.get("last_chat_msg") != user_msg:
            # Save user message
            st.session_state.chat_history.append(
                {"role": "user", "text": user_msg}
            )

            # Get reply
            reply = handle_chat(user_msg)

            # Save assistant message
            st.session_state.chat_history.append(
                {"role": "assistant", "text": reply}
            )

            # Remember last processed message
            st.session_state.last_chat_msg = user_msg
            # ✅ No manual clear, no st.rerun() needed


def summarize_transactions(tx_list):
    """Return simple stats from the transaction list."""
    if not tx_list:
        return {
            "income": 0.0,
            "spending": 0.0,
            "net": 0.0,
        }

    income = 0.0
    spending = 0.0

    for tx in tx_list:
        # tx["amount"] > 0 => spending, < 0 => income (Plaid style)
        amt = float(tx.get("amount", 0) or 0)
        if amt > 0:
            spending += amt
        elif amt < 0:
            income += -amt  # flip sign so income is positive

    return {
        "income": income,
        "spending": spending,
        "net": income - spending,
    }



# ---------- MIDDLE: MAIN CONTENT ----------
with main_col:
    section = st.session_state.active_section

        # ===== DASHBOARD =====
    if section == "dashboard":
        st.title("FinBuddy Dashboard")

        name = st.session_state.profile_name or "there"
        st.write(f"Welcome, **{name}** 👋")

        # ---- compute basic stats from transactions ----
        txns = st.session_state.transactions or []
        total_spent = 0.0
        total_income = 0.0
        category_totals = {}

        for t in txns:
            amount = float(t.get("amount", 0))
            name_t = str(t.get("name", "")).lower()
            cat = str(t.get("category", "")).lower()

            # simple category guess if category missing
            key = cat or (
                "groceries" if "grocery" in name_t else
                "rent" if "rent" in name_t else
                "transport" if "uber" in name_t or "taxi" in name_t or "bus" in name_t else
                "income" if amount < 0 else   # income = money coming IN
                "other"
            )

            if key not in category_totals:
                category_totals[key] = 0.0

            # Plaid-style: amount > 0 => spending, amount < 0 => income
            if amount > 0:
                total_spent += amount
                category_totals[key] += amount
            elif amount < 0:
                total_income += -amount  # store income as positive
                category_totals[key] += -amount

        total_budget = (
            st.session_state.budget_groceries
            + st.session_state.budget_rent
            + st.session_state.budget_transport
            + st.session_state.budget_entertainment
            + st.session_state.budget_other
        )

        # rough estimate of "available this month"
        estimated_available = max(
            0.0,
            float(st.session_state.monthly_income) - total_spent
        )

        # ---- TOP METRICS ROW (like big cards) ----
        col_a, col_b, col_c, col_d = st.columns(4)

        with col_a:
            st.metric("Monthly income", f"${st.session_state.monthly_income:.2f}")

        with col_b:
            st.metric("Total spending (data)", f"${total_spent:.2f}")

        with col_c:
            st.metric("Planned monthly budget", f"${total_budget:.2f}")

        with col_d:
            status = "Connected ✅" if st.session_state.access_token else "Not connected ❌"
            st.metric(
                "Estimated available this month",
                f"${estimated_available:.2f}",
                help="Income − expenses from your transactions"
            )
            st.caption(status)

        st.markdown("---")

        # ---- CHARTS: income vs spending + category breakdown ----
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Income vs spending")

            # simple bar comparison
            comp_df = pd.DataFrame(
                {
                    "type": ["Income", "Spending"],
                    "amount": [total_income, total_spent],
                }
            ).set_index("type")

            st.bar_chart(comp_df, use_container_width=True)

        with col2:
            st.subheader("Spending by category")

            # filter only expense categories (positive amounts of spending)
            cat_expenses = {k: v for k, v in category_totals.items() if k not in ("income", "") and v > 0}

            if cat_expenses:
                cat_df = pd.DataFrame(
                    {"category": list(cat_expenses.keys()), "amount": list(cat_expenses.values())}
                ).set_index("category")
                st.bar_chart(cat_df, use_container_width=True)
            else:
                st.info("No categorized spending yet. Once you have more transactions, you'll see a breakdown here.")

        st.markdown("---")

        # ---- RECENT TRANSACTIONS TABLE ----
        st.subheader("Recent transactions")

        if txns:
            df = pd.DataFrame(txns)
            # make it look nicer if keys exist
            # e.g., keep common columns if present
            preferred_cols = [c for c in ["date", "name", "category", "amount"] if c in df.columns]
            if preferred_cols:
                df = df[preferred_cols]
            st.dataframe(df.head(8), use_container_width=True)
        else:
            st.info("No transactions loaded yet. Link your bank on the **Bank connect** page and load them from **Spending & budget**.")

    
    

    # ===== PROFILE =====
    elif section == "profile":
        st.title("Profile")

        st.write("Set your basic details so FinBuddy can personalize your insights.")

        st.session_state.profile_name = st.text_input(
            "Name", value=st.session_state.profile_name, placeholder="e.g., Deep"
        )
        st.session_state.monthly_income = st.number_input(
            "Monthly income (after tax)",
            min_value=0.0,
            value=float(st.session_state.monthly_income),
            step=100.0,
        )

        st.success("Profile info is saved automatically.")

        # ===== BANK CONNECT =====
    elif section == "bank":
        st.title("Bank connection")

        st.write(
            "Link your sandbox bank so FinBuddy can see your transactions and give insights."
        )

        col1, col2 = st.columns(2)

        # LEFT COLUMN: quick sandbox + (optional) manual link flow
        with col1:
            # Quick auto-connect button
            st.markdown("#### Quick connect (sandbox)")
            if st.button("🔌 Connect sandbox bank (auto)"):
                try:
                    res = sandbox_auto_connect()
                    # backend returns: {"ok": True, "item_id": "..."}
                    st.session_state.item_id = res.get("item_id")
                    st.session_state.access_token = "linked" if res.get("ok") else None
                    st.success("Sandbox bank connected successfully!")
                except ApiError as e:
                    st.error(str(e))

            st.markdown("---")
            st.markdown("#### 1. Generate link token (optional)")

            if st.button("Generate link token"):
                try:
                    data = create_link_token()
                    st.session_state.link_token = data.get("link_token")
                    st.session_state.sandbox_url = data.get("sandbox_url")
                    st.success("Link token created.")
                except ApiError as e:
                    st.error(str(e))

            if st.session_state.link_token:
                st.code(st.session_state.link_token, language="text")

            if st.session_state.sandbox_url:
                st.markdown(
                    f"[Open sandbox bank connect page]({st.session_state.sandbox_url})",
                    unsafe_allow_html=True,
                )

        # RIGHT COLUMN: manual public_token exchange (fallback)
        with col2:
            st.markdown("#### 2. Connect account (manual)")

            st.session_state.public_token = st.text_input(
                "Paste the public_token from sandbox",
                value=st.session_state.public_token or "",
            )

            if st.button("Connect bank (manual)"):
                if not st.session_state.public_token:
                    st.error("Paste a public_token first.")
                else:
                    try:
                        res = exchange_public_token(st.session_state.public_token)
                        # backend returns: {"ok": True, "item_id": "..."}
                        st.session_state.item_id = res.get("item_id")
                        st.session_state.access_token = "linked" if res.get("ok") else None
                        st.success("Bank connected successfully!")
                    except ApiError as e:
                        st.error(str(e))

            st.markdown("#### Status")
            st.write("Link token created:", bool(st.session_state.link_token))
            st.write("Bank linked:", bool(st.session_state.access_token))
            st.write("Item ID:", st.session_state.item_id or "—")


    # ===== SPENDING & BUDGET =====
    elif section == "spending_budget":
        st.title("Spending & budget")

        st.write("Set your monthly budgets and compare them to your real spending.")

        colb1, colb2 = st.columns(2)

        with colb1:
            st.subheader("Monthly budgets")
            st.session_state.budget_groceries = st.number_input(
                "Groceries",
                min_value=0.0,
                value=float(st.session_state.budget_groceries),
                step=50.0,
            )
            st.session_state.budget_rent = st.number_input(
                "Rent / Housing",
                min_value=0.0,
                value=float(st.session_state.budget_rent),
                step=50.0,
            )
            st.session_state.budget_transport = st.number_input(
                "Transport",
                min_value=0.0,
                value=float(st.session_state.budget_transport),
                step=20.0,
            )
            st.session_state.budget_entertainment = st.number_input(
                "Entertainment",
                min_value=0.0,
                value=float(st.session_state.budget_entertainment),
                step=20.0,
            )
            st.session_state.budget_other = st.number_input(
                "Other",
                min_value=0.0,
                value=float(st.session_state.budget_other),
                step=20.0,
            )

        with colb2:
            st.subheader("Transactions")

            if not st.session_state.access_token:
                st.warning("Bank not connected. Go to **Bank connect** to link a sandbox account.")
            else:
                if st.button("Load latest transactions"):
                    try:
                        data = fetch_transactions()
                        st.session_state.transactions = data.get("transactions", [])
                        st.success("Transactions updated.")
                    except ApiError as e:
                        st.error(str(e))

                txns = st.session_state.transactions or []
                if txns:
                    df = pd.DataFrame(txns)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No transactions loaded yet.")

        # Simple summary
        txns = st.session_state.transactions or []
        total_spent = 0.0
        for t in txns:
            amount = float(t.get("amount", 0))
            if amount < 0:
                total_spent += -amount

        total_budget = (
            st.session_state.budget_groceries
            + st.session_state.budget_rent
            + st.session_state.budget_transport
            + st.session_state.budget_entertainment
            + st.session_state.budget_other
        )

        st.markdown("---")
        st.subheader("Summary")
        st.write(f"Total planned budget: **${total_budget:.2f}**")
        st.write(f"Observed spending (all expenses): **${total_spent:.2f}**")
        if total_budget > 0:
            diff = total_budget - total_spent
            if diff >= 0:
                st.success(f"You are **${diff:.2f} under** your total planned budget.")
            else:
                st.error(f"You are **${-diff:.2f} over** your total planned budget.")
