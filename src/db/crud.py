"""
RiskLens AI - Data Access Layer (CRUD)
All read/write operations against the relational schema go through here,
so the rest of the app never writes raw SQL inline.
"""
import json
from sqlalchemy import text
from src.db.connection import get_engine


def log_audit(entity_type: str, entity_id: int, action: str, details: dict, performed_by: str = "system"):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("""INSERT INTO audit_logs (entity_type, entity_id, action, performed_by, details)
                     VALUES (:et, :eid, :act, :by, :det)"""),
            {"et": entity_type, "eid": entity_id, "act": action,
             "by": performed_by, "det": json.dumps(details, default=str)}
        )


def insert_customer(data: dict) -> int:
    engine = get_engine()
    with engine.begin() as conn:
        result = conn.execute(
            text("""INSERT INTO customers
                    (full_name, age, occupation, employment_type, years_of_employment,
                     annual_income, credit_score, open_accounts, previous_defaults)
                    VALUES (:full_name, :age, :occupation, :employment_type, :years_of_employment,
                            :annual_income, :credit_score, :open_accounts, :previous_defaults)"""),
            data
        )
        customer_id = result.lastrowid
    log_audit("customer", customer_id, "CREATE", data)
    return customer_id


def insert_loan_application(data: dict) -> int:
    engine = get_engine()
    with engine.begin() as conn:
        result = conn.execute(
            text("""INSERT INTO loan_applications
                    (customer_id, loan_amount, loan_purpose, existing_debt, monthly_emi, application_status)
                    VALUES (:customer_id, :loan_amount, :loan_purpose, :existing_debt, :monthly_emi, 'PENDING')"""),
            data
        )
        app_id = result.lastrowid
    log_audit("application", app_id, "CREATE", data)
    return app_id


def insert_risk_assessment(application_id: int, metrics: dict) -> int:
    engine = get_engine()
    payload = {"application_id": application_id, **metrics}
    with engine.begin() as conn:
        result = conn.execute(
            text("""INSERT INTO risk_assessments
                    (application_id, debt_to_income_ratio, emi_to_income_ratio,
                     loan_to_income_ratio, credit_utilization_score, financial_risk_score)
                    VALUES (:application_id, :dti, :eti, :lti, :cu_score, :financial_risk_score)"""),
            payload
        )
        return result.lastrowid


def insert_prediction(application_id: int, pred: dict) -> int:
    engine = get_engine()
    payload = {
        "application_id": application_id,
        "model_name": pred["model_name"],
        "default_probability": pred["default_probability"],
        "risk_score": pred["risk_score"],
        "risk_category": pred["risk_category"],
        "recommendation": pred["recommendation"],
        "top_risk_drivers": json.dumps(pred["top_risk_drivers"]),
    }
    engine = get_engine()
    with engine.begin() as conn:
        result = conn.execute(
            text("""INSERT INTO predictions
                    (application_id, model_name, default_probability, risk_score,
                     risk_category, recommendation, top_risk_drivers)
                    VALUES (:application_id, :model_name, :default_probability, :risk_score,
                            :risk_category, :recommendation, :top_risk_drivers)"""),
            payload
        )
        pred_id = result.lastrowid
    log_audit("prediction", pred_id, "PREDICT", pred)

    # update application status based on recommendation
    status_map = {"APPROVE": "APPROVED", "REVIEW": "UNDER_REVIEW", "REJECT": "REJECTED"}
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE loan_applications SET application_status=:status WHERE application_id=:aid"),
            {"status": status_map.get(pred["recommendation"], "PENDING"), "aid": application_id}
        )
    return pred_id


def fetch_summary_view():
    """Returns the full joined dataset for dashboards."""
    engine = get_engine()
    query = text("""
        SELECT c.customer_id, c.full_name, c.age, c.employment_type, c.annual_income,
               c.credit_score, la.application_id, la.loan_amount, la.loan_purpose,
               la.application_status, la.application_date,
               ra.debt_to_income_ratio, ra.financial_risk_score,
               p.default_probability, p.risk_score, p.risk_category, p.recommendation,
               p.top_risk_drivers
        FROM customers c
        JOIN loan_applications la ON c.customer_id = la.customer_id
        LEFT JOIN risk_assessments ra ON la.application_id = ra.application_id
        LEFT JOIN predictions p ON la.application_id = p.application_id
        ORDER BY la.application_id DESC
    """)
    with engine.begin() as conn:
        rows = conn.execute(query).mappings().all()
    return [dict(r) for r in rows]
