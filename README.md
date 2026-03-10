# FinBuddy — AI Financial Assistant

> Ask "Should I buy $150 ALDO shoes?" → Get a verdict, your remaining balance, and how many hours of work it costs.

**Live app:** https://verdant-seahorse-32c03c.netlify.app

---

## What it does

- Connect your bank accounts via Plaid
- Track spending by category with charts
- Chat with AI about your finances
- Set budgets and track bills
- Multi-user — anyone can sign up

---

## Tech Stack

- **Backend:** FastAPI (Python), 21 endpoints
- **Database:** PostgreSQL (Supabase)
- **ETL:** 3 pipelines — fetch from Plaid → categorize → store
- **AI:** Anthropic API with live financial context
- **Auth:** JWT + bcrypt
- **Frontend:** HTML/CSS/JS, Chart.js
- **Deployed:** Render (backend) + Netlify (frontend) + Supabase (DB) — **$0/month**

---

## Run Locally

**1. Clone**
```bash
git clone https://github.com/dmandaliya/FinBuddy.git
cd FinBuddy
```

**2. Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env` (copy from `.env.example`) and fill in your keys:
```
DATABASE_URL=postgresql://...
PLAID_CLIENT_ID=...
PLAID_SECRET=...
ANTHROPIC_API_KEY=sk-ant-...
JWT_SECRET=any-long-random-string
```

```bash
uvicorn main:app --reload --port 8001
```

**3. Frontend**
```bash
cd frontend
python3 -m http.server 8000
```

Open `http://localhost:8000`

---

## Deploy (Free)

| Service | Purpose | Cost |
|---|---|---|
| [Supabase](https://supabase.com) | PostgreSQL database | Free forever |
| [Render](https://render.com) | FastAPI backend | Free |
| [Netlify](https://netlify.com) | Frontend hosting | Free |

**Steps:**
1. Create Supabase project → copy Session Pooler connection string → use as `DATABASE_URL`
2. Deploy backend on Render → set root directory to `backend` → add env vars
3. Deploy frontend on Netlify → set publish directory to `frontend`
4. Update `frontend/js/config.js` with your Render URL → push to GitHub

---

## API Endpoints

| Method | Route | Description |
|---|---|---|
| POST | `/auth/signup` | Create account |
| POST | `/auth/login` | Login |
| GET | `/auth/me` | Current user |
| POST | `/plaid/create_link_token` | Start bank linking |
| POST | `/plaid/exchange_public_token` | Save bank connection |
| GET | `/plaid/accounts` | List linked accounts |
| POST | `/plaid/sync` | Fetch latest transactions |
| GET | `/api/transactions` | All transactions |
| GET | `/api/transactions/summary` | Spending by category |
| GET | `/api/transactions/recent` | Last 10 transactions |
| GET/POST | `/api/budgets` | Budgets |
| GET/POST | `/api/bills` | Bills |
| GET/POST | `/api/income` | Income sources |
| POST | `/ai/chat` | AI financial assistant |

---

## Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | Supabase PostgreSQL connection string |
| `PLAID_CLIENT_ID` | From [dashboard.plaid.com](https://dashboard.plaid.com) |
| `PLAID_SECRET` | Plaid sandbox or development secret |
| `PLAID_ENV` | `sandbox` or `development` |
| `ANTHROPIC_API_KEY` | From [console.anthropic.com](https://console.anthropic.com) |
| `JWT_SECRET` | Any long random string |
