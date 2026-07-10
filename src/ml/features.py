"""
RiskLens AI - Financial Metrics & Feature Engineering
This module encodes the deterministic (rule-based) credit risk logic that
a real risk team uses BEFORE any ML model is consulted. The ML model then
learns to refine/predict on top of these engineered ratios.
"""
import numpy as np
import pandas as pd

EPS = 1e-6


def compute_financial_metrics(row: dict) -> dict:
    """
    Computes standard banking risk ratios for a single applicant.
    row keys expected: annual_income, loan_amount, existing_debt,
    monthly_emi, credit_score, previous_defaults, open_accounts
    """
    annual_income = max(float(row["annual_income"]), EPS)
    monthly_income = annual_income / 12

    dti = (float(row["existing_debt"]) + float(row["loan_amount"])) / annual_income
    eti = float(row["monthly_emi"]) / max(monthly_income, EPS)
    lti = float(row["loan_amount"]) / annual_income

    # Credit utilization proxy: more open accounts + lower score => higher utilization risk
    credit_score = float(row["credit_score"])
    cu_score = np.clip((900 - credit_score) / 600, 0, 1) * 0.7 + \
        np.clip(float(row.get("open_accounts", 0)) / 15, 0, 1) * 0.3

    # ---- Rule-based Financial Risk Score (0-100), fully transparent ----
    score = 0
    score += np.clip(dti, 0, 2) / 2 * 35          # 35 pts max - debt-to-income
    score += np.clip(eti, 0, 1.2) / 1.2 * 25       # 25 pts max - EMI burden
    score += np.clip((900 - credit_score) / 600, 0, 1) * 25  # 25 pts - credit score
    score += min(float(row.get("previous_defaults", 0)), 3) / 3 * 15  # 15 pts - default history

    financial_risk_score = round(float(np.clip(score, 0, 100)), 2)

    return {
        "dti": round(dti, 4),
        "eti": round(eti, 4),
        "lti": round(lti, 4),
        "cu_score": round(float(cu_score), 4),
        "financial_risk_score": financial_risk_score,
    }


def build_feature_row(row: dict) -> pd.DataFrame:
    """Builds the exact feature vector the ML model was trained on."""
    metrics = compute_financial_metrics(row)
    features = {
        "age": float(row["age"]),
        "years_of_employment": float(row.get("years_of_employment", 0)),
        "annual_income": float(row["annual_income"]),
        "loan_amount": float(row["loan_amount"]),
        "existing_debt": float(row["existing_debt"]),
        "monthly_emi": float(row["monthly_emi"]),
        "credit_score": float(row["credit_score"]),
        "open_accounts": float(row.get("open_accounts", 0)),
        "previous_defaults": float(row.get("previous_defaults", 0)),
        "debt_to_income_ratio": metrics["dti"],
        "emi_to_income_ratio": metrics["eti"],
        "loan_to_income_ratio": metrics["lti"],
        "credit_utilization_score": metrics["cu_score"],
    }
    return pd.DataFrame([features]), metrics


FEATURE_COLUMNS = [
    "age", "years_of_employment", "annual_income", "loan_amount",
    "existing_debt", "monthly_emi", "credit_score", "open_accounts",
    "previous_defaults", "debt_to_income_ratio", "emi_to_income_ratio",
    "loan_to_income_ratio", "credit_utilization_score",
]


def risk_category_from_score(score: float) -> str:
    from src.config import RISK_BANDS
    for cat, (lo, hi) in RISK_BANDS.items():
        if lo <= score < hi:
            return cat
    return "CRITICAL"


def recommendation_from_category(category: str) -> str:
    from src.config import RECOMMENDATION_RULES
    return RECOMMENDATION_RULES.get(category, "REVIEW")
