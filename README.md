# FinBuddy — AI Financial Assistant

A full-stack personal finance app that connects real bank accounts, tracks spending, and answers money questions using AI.

> "Should I buy those $150 ALDO shoes?" → FinBuddy tells you the verdict, your remaining balance, and how many hours of work it costs.

---

## Features

- **Bank linking** via Plaid (sandbox + real accounts, multiple accounts supported)
- **AI chat** powered by Claude — asks context-aware questions using your live financial data
- **Affordability analysis** — translates any purchase into dollar impact + hours of work
- **Spending dashboard** — categorized spending, monthly trends, Chart.js visualizations
- **Budget & bills tracker** — set category budgets, track recurring bills
- **Multi-user** — anyone can sign up and connect their own accounts
- **JWT auth** with bcrypt password hashing

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python), 21 REST endpoints |
| Database | PostgreSQL, SQLAlchemy ORM, 7 tables |
| ETL | 3-pipeline system: ingest → transform → load |
| AI | Anthropic Claude (`claude-sonnet-4-6`) |
| Bank Data | Plaid API |
| Auth | JWT + bcrypt (passlib) |
| Frontend | Vanilla HTML/CSS/JS, Chart.js |
| Backend Deploy | Render.com |
| Frontend Deploy | Netlify |

---

## Project Structure

```
FinBuddy/
├── backend/
│   ├── main.py              # FastAPI app, CORS, router registration
│   ├── models.py            # 7 SQLAlchemy models (User, Account, Transaction, ...)
│   ├── database.py          # PostgreSQL connection
│   ├── requirements.txt
│   ├── .env.example
│   ├── etl/
│   │   ├── ingest.py        # Fetch from Plaid with pagination + retry logic
│   │   ├── transform.py     # Normalize 15+ Plaid categories → 9 buckets
│   │   └── load.py          # Upsert to PostgreSQL, deduplicate transactions
│   └── routes/
│       ├── auth.py          # Signup, login, JWT
│       ├── plaid_routes.py  # Bank linking, account sync
│       ├── transactions.py  # Transaction queries + summary
│       ├── budget.py        # Budgets, bills, income sources
│       └── ai.py            # Claude chat with live financial context
├── frontend/
│   ├── index.html           # Dashboard
│   ├── chat.html            # AI chat
│   ├── bank.html            # Bank linking (Plaid Link)
│   ├── transactions.html
│   ├── budget.html
│   ├── login.html
│   ├── js/
│   │   ├── config.js        # Auto-switches API URL (local vs production)
│   │   ├── api.js
│   │   ├── auth.js
│   │   └── ...
│   ├── css/style.css        # Pastel Garden theme
│   └── netlify.toml
├── render.yaml              # Render Blueprint (backend + PostgreSQL)
└── start.py                 # Local dev launcher
```

---

## Local Setup

### 1. Clone the repo

```bash
git clone https://github.com/dmandaliya/FinBuddy.git
cd FinBuddy
```

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file (copy from `.env.example`):

```env
DATABASE_URL=postgresql://your_user@localhost:5432/finbuddy
PLAID_CLIENT_ID=your_plaid_client_id
PLAID_SECRET=your_plaid_secret
PLAID_ENV=sandbox
ANTHROPIC_API_KEY=sk-ant-...
JWT_SECRET=pick-a-long-random-string
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=72
FRONTEND_URL=http://localhost:8000
```

Create the database:

```bash
createdb finbuddy
```

Start the backend:

```bash
uvicorn main:app --reload --port 8001
```

### 3. Frontend

```bash
cd frontend
python3 -m http.server 8000
```

Open `http://localhost:8000`

---

## Deployment

### Backend → Render

1. Go to [render.com](https://render.com) → New → Blueprint
2. Connect this GitHub repo — Render auto-reads `render.yaml`
3. Add environment variables manually (Plaid keys, Anthropic key, JWT secret)
4. Deploy — you'll get a URL like `https://finbuddy-api.onrender.com`

### Frontend → Netlify

1. Go to [netlify.com](https://netlify.com)
2. Drag and drop the `frontend/` folder
3. Done — instant shareable URL

### After both are deployed

Update `frontend/js/config.js`:
```js
const PROD_API = "https://finbuddy-api.onrender.com"; // your actual Render URL
```

Add `FRONTEND_URL=https://your-app.netlify.app` to Render environment variables.

---

## API Endpoints

| Method | Route | Description |
|---|---|---|
| POST | `/auth/signup` | Create account |
| POST | `/auth/login` | Get JWT token |
| GET | `/auth/me` | Current user |
| POST | `/plaid/create_link_token` | Start Plaid flow |
| POST | `/plaid/exchange_public_token` | Save bank connection |
| GET | `/plaid/accounts` | List linked accounts |
| POST | `/plaid/sync` | Pull latest transactions |
| GET | `/api/transactions` | Paginated transactions |
| GET | `/api/transactions/summary` | Spending by category |
| GET | `/api/transactions/recent` | Last 10 transactions |
| GET/POST | `/api/budgets` | Budget CRUD |
| GET/POST | `/api/bills` | Bills CRUD |
| GET/POST | `/api/income` | Income sources CRUD |
| POST | `/ai/chat` | AI financial assistant |

---

## Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `PLAID_CLIENT_ID` | From [dashboard.plaid.com](https://dashboard.plaid.com) |
| `PLAID_SECRET` | Plaid sandbox or development secret |
| `PLAID_ENV` | `sandbox` or `development` |
| `ANTHROPIC_API_KEY` | From [console.anthropic.com](https://console.anthropic.com) |
| `JWT_SECRET` | Any long random string |
| `JWT_EXPIRE_HOURS` | Token expiry (default: 72) |
| `FRONTEND_URL` | Your Netlify URL (for CORS) |

---

## Real Bank Connections

The app is configured for Plaid **sandbox** by default (test accounts, no real data).

To connect real bank accounts:
1. Apply for Plaid **Development** access at [dashboard.plaid.com](https://dashboard.plaid.com)
2. Set `PLAID_ENV=development` and use your development secret
3. Users can then link real Chase, Bank of America, Wells Fargo, etc. accounts

---

## License

MIT
