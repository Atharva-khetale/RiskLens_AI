"""
RiskLens AI - Central Configuration
Loads environment variables and exposes app-wide constants.
"""
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---- Database ----
DB_ENGINE = os.getenv("DB_ENGINE", "sqlite")

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "risklens_ai")

SQLITE_PATH = os.path.join(BASE_DIR, os.getenv("SQLITE_PATH", "data/risklens.db"))

def get_database_url() -> str:
    if DB_ENGINE == "mysql":
        return (f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
                f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}")
    os.makedirs(os.path.dirname(SQLITE_PATH), exist_ok=True)
    return f"sqlite:///{SQLITE_PATH}"

# ---- Paths ----
MODEL_DIR = os.path.join(BASE_DIR, "models")
DATA_DIR = os.path.join(BASE_DIR, "data")
REPORT_DIR = os.path.join(BASE_DIR, "data", "reports")
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

BEST_MODEL_PATH = os.path.join(MODEL_DIR, "best_model.joblib")
MODEL_META_PATH = os.path.join(MODEL_DIR, "model_meta.json")

# ---- Risk thresholds ----
RISK_BANDS = {
    "LOW":      (0, 30),
    "MEDIUM":   (30, 55),
    "HIGH":     (55, 80),
    "CRITICAL": (80, 101),
}

RECOMMENDATION_RULES = {
    "LOW": "APPROVE",
    "MEDIUM": "REVIEW",
    "HIGH": "REJECT",
    "CRITICAL": "REJECT",
}
