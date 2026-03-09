"""
FinBuddy launcher — starts the backend API and opens the frontend.
Run with: python start.py
"""

import subprocess
import webbrowser
import time
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "backend")
FRONTEND = os.path.join(ROOT, "frontend")
VENV_PYTHON = os.path.join(ROOT, ".venv", "bin", "python")

print("=" * 50)
print("  FinBuddy 💰")
print("=" * 50)

# Start FastAPI backend
print("\n▶ Starting backend (FastAPI on port 8001)...")
backend_proc = subprocess.Popen(
    [VENV_PYTHON, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8001", "--reload"],
    cwd=BACKEND,
)

# Give it 2 seconds to boot before opening the browser
time.sleep(2)

# Serve the frontend with Python's built-in HTTP server on port 8080
print("▶ Starting frontend (port 8080)...")
frontend_proc = subprocess.Popen(
    [sys.executable, "-m", "http.server", "8080"],
    cwd=FRONTEND,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

time.sleep(1)

# Open the app in the browser
url = "http://localhost:8080/login.html"
print(f"\n✅ FinBuddy is running!")
print(f"   Frontend: http://localhost:8080/login.html")
print(f"   Backend:  http://localhost:8001")
print(f"   API docs: http://localhost:8001/docs")
print("\nPress Ctrl+C to stop.\n")

webbrowser.open(url)

try:
    backend_proc.wait()
except KeyboardInterrupt:
    print("\nShutting down...")
    backend_proc.terminate()
    frontend_proc.terminate()
