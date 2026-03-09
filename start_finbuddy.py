import subprocess
import os
import time

# Paths
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON = os.path.join(PROJECT_ROOT, ".venv", "bin", "python")
FRONTEND_APP = os.path.join(PROJECT_ROOT, "frontend", "app.py")
BACKEND_APP = os.path.join(PROJECT_ROOT, "backend", "main.py")

# Start backend (FastAPI / Uvicorn)
backend_cmd = [
    VENV_PYTHON,
    "-m", "uvicorn",
    "main:app",
    "--host", "127.0.0.1",
    "--port", "8001",
    "--reload"
]

backend_process = subprocess.Popen(
    backend_cmd,
    cwd=os.path.join(PROJECT_ROOT, "backend")
)

time.sleep(2)  # give backend time to start

# Start frontend (Streamlit)
frontend_cmd = [
    VENV_PYTHON,
    "-m", "streamlit",
    "run",
    FRONTEND_APP
]

frontend_process = subprocess.Popen(
    frontend_cmd,
    cwd=PROJECT_ROOT
)

print("FinBuddy started successfully!")
print("Backend running on: http://127.0.0.1:8001")
print("Frontend running on: http://localhost:8501")
print("If the browser does not open automatically, open http://localhost:8501 manually.")
print("Do not close this window while using FinBuddy.")

# Wait until Streamlit stops
frontend_process.wait()
# When frontend exits, stop backend too
backend_process.terminate()
