"""
Local Development Bootstrap (Windows / Python 3.13+)
Starts the backend with SQLite instead of PostgreSQL — no Docker needed.

Usage:
  py -3.13 dev_start.py

Environment set automatically:
  DATABASE_URL = sqlite+aiosqlite:///./drishti_dev.db
  JWT_SECRET   = dev-secret-local
  UPLOAD_DIR   = ./uploads
"""
import os
import sys
import subprocess

# ─── Set dev environment ─────────────────────────────────────
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./drishti_dev.db")
os.environ.setdefault("JWT_SECRET", "dev-secret-local-min32-chars-padded-xx")
os.environ.setdefault("JWT_ALGO", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MIN", "60")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "7")
os.environ.setdefault("UPLOAD_DIR", "./uploads")
os.environ.setdefault("MODEL_DIR", "./assets/models")
os.environ.setdefault("DEMO_IMAGES_DIR", "./assets/demo")
os.environ.setdefault("DOCTOR_CSV_PATH", "./assets/seed/doctors.csv")
os.environ.setdefault("HOSPITAL_CSV_PATH", "./assets/seed/hospitals.csv")
os.environ.setdefault("OFFICER_CSV_PATH", "./assets/seed/officers.csv")
os.environ.setdefault("PATIENT_CSV_PATH", "./assets/seed/patients.csv")
os.environ.setdefault("CORS_ORIGINS", '["http://localhost:3000","http://localhost:8000"]')
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("APP_VERSION", "1.0.0-mvp-dev")

print("=" * 55)
print("  DRISHTI-LENS — Local Dev Server")
print("  DB   : SQLite (drishti_dev.db)")
print("  API  : http://localhost:8000")
print("  Docs : http://localhost:8000/docs")
print("=" * 55)
print()
print("  Tip: Run 'py -3.13 scripts/seed_local.py' first")
print()

# ─── Start uvicorn ───────────────────────────────────────────
# Use py -3.13 explicitly since pydantic-core requires <= Python 3.13
import shutil
python313 = shutil.which("py")
cmd = [python313, "-3.13", "-m", "uvicorn", "main:app",
       "--host", "0.0.0.0",
       "--port", "8000",
       "--reload",
       "--log-level", "info"] if python313 else [
    sys.executable, "-m", "uvicorn", "main:app",
    "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "info"
]
subprocess.run(cmd)
