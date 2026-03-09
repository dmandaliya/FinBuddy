"""
FinBuddy Backend — FastAPI
Wires together all routes and sets up the database on startup.
Run via: uvicorn main:app --host 127.0.0.1 --port 8001 --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

# Import the database engine and models so tables get created on startup
from database import engine
import models  # noqa — just importing this registers all SQLAlchemy models

from routes.auth import router as auth_router
from routes.plaid_routes import router as plaid_router
from routes.transactions import router as tx_router
from routes.budget import router as budget_router
from routes.ai import router as ai_router

# Create all tables if they don't exist yet.
# In production you'd use Alembic migrations instead.
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="FinBuddy API", version="2.0")

# CORS — allow localhost for dev and Netlify URL for production.
# FRONTEND_URL env var is set in Render dashboard after you deploy Netlify.
import os as _os
_frontend = _os.getenv("FRONTEND_URL", "*")
_origins = ["http://localhost:8080", "http://127.0.0.1:8080"]
if _frontend != "*":
    _origins.append(_frontend)
else:
    _origins = ["*"]  # dev fallback — tighten once Netlify URL is known

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all route groups
app.include_router(auth_router)
app.include_router(plaid_router)
app.include_router(tx_router)
app.include_router(budget_router)
app.include_router(ai_router)


@app.get("/")
def root():
    return {"message": "FinBuddy API is running", "version": "2.0"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "finbuddy-backend"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
