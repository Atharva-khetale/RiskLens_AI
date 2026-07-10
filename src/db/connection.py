"""
RiskLens AI - Database Connection Layer
Uses SQLAlchemy Core for portability between MySQL (production)
and SQLite (zero-config local/demo mode).
"""
from sqlalchemy import create_engine, text, MetaData
from src.config import get_database_url, DB_ENGINE

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        url = get_database_url()
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        _engine = create_engine(url, connect_args=connect_args, pool_pre_ping=True)
        _ensure_schema(_engine)
    return _engine


def _ensure_schema(engine):
    """Creates tables if they don't exist. Uses ANSI-compatible DDL
    that works on both MySQL and SQLite (schema.sql is the MySQL
    canonical version used in production deployments)."""
    ddl = """
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        age INTEGER NOT NULL,
        occupation TEXT,
        employment_type TEXT NOT NULL,
        years_of_employment REAL DEFAULT 0,
        annual_income REAL NOT NULL,
        credit_score INTEGER NOT NULL,
        open_accounts INTEGER DEFAULT 0,
        previous_defaults INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS loan_applications (
        application_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        loan_amount REAL NOT NULL,
        loan_purpose TEXT,
        existing_debt REAL DEFAULT 0,
        monthly_emi REAL DEFAULT 0,
        application_status TEXT DEFAULT 'PENDING',
        application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    );

    CREATE TABLE IF NOT EXISTS risk_assessments (
        assessment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        application_id INTEGER NOT NULL,
        debt_to_income_ratio REAL,
        emi_to_income_ratio REAL,
        loan_to_income_ratio REAL,
        credit_utilization_score REAL,
        financial_risk_score REAL,
        assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (application_id) REFERENCES loan_applications(application_id)
    );

    CREATE TABLE IF NOT EXISTS predictions (
        prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        application_id INTEGER NOT NULL,
        model_name TEXT,
        default_probability REAL,
        risk_score REAL,
        risk_category TEXT,
        recommendation TEXT,
        top_risk_drivers TEXT,
        predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (application_id) REFERENCES loan_applications(application_id)
    );

    CREATE TABLE IF NOT EXISTS audit_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type TEXT,
        entity_id INTEGER,
        action TEXT,
        performed_by TEXT DEFAULT 'system',
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    with engine.begin() as conn:
        for stmt in ddl.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                conn.execute(text(stmt))
