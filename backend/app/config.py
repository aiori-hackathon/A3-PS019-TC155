import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

def normalize_database_url(url: str) -> str:
    """Use the installed psycopg v3 driver for provider PostgreSQL URLs."""
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url.removeprefix("postgres://")
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url.removeprefix("postgresql://")
    return url

DATABASE_URL = normalize_database_url(os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'privexis.db'}"))
SECRET_KEY = os.getenv("PRIVEXIS_SECRET_KEY", "development-only-change-this-secret-key")
ENVIRONMENT = os.getenv("PRIVEXIS_ENV", "development")
FRONTEND_ORIGIN = os.getenv("PRIVEXIS_FRONTEND_ORIGIN", "http://localhost:3000")
UPLOAD_DIR = Path(os.getenv("PRIVEXIS_UPLOAD_DIR", str(BASE_DIR / "uploads"))).resolve()
MAX_UPLOAD_MB = int(os.getenv("PRIVEXIS_MAX_UPLOAD_MB", "15"))
SAMPLE_ROWS = min(int(os.getenv("PRIVEXIS_SCAN_SAMPLE_ROWS", "500")), 5000)
