"""
RiskLens AI - Prediction & Explainable AI (SHAP) Engine
Loads the best trained model, scores a borrower, blends the ML default
probability with the rule-based financial risk score into a single
0-100 Risk Score, assigns a risk category, and generates a human
readable explanation of WHY using SHAP values.
"""
import os
import joblib
import numpy as np
import pandas as pd

from src.config import BEST_MODEL_PATH
from src.ml.features import (build_feature_row, risk_category_from_score,
                              recommendation_from_category, FEATURE_COLUMNS)

_bundle = None
_explainer = None

FRIENDLY_NAMES = {
    "debt_to_income_ratio": "Debt-to-Income Ratio",
    "emi_to_income_ratio": "EMI-to-Income Ratio",
    "loan_to_income_ratio": "Loan-to-Income Ratio",
    "credit_utilization_score": "Credit Utilization",
    "credit_score": "Credit Score",
    "previous_defaults": "Previous Default History",
    "annual_income": "Annual Income",
    "loan_amount": "Loan Amount",
    "existing_debt": "Existing Debt",
    "monthly_emi": "Monthly EMI",
    "age": "Age",
    "years_of_employment": "Years of Employment",
    "open_accounts": "Number of Open Accounts",
}


def _load_bundle():
    global _bundle
    if _bundle is None:
        if not os.path.exists(BEST_MODEL_PATH):
            from src.ml.train import train_all_models
            train_all_models()
        _bundle = joblib.load(BEST_MODEL_PATH)
    return _bundle


def _get_explainer(model, model_name, background: pd.DataFrame):
    global _explainer
    import shap
    if _explainer is None:
        if model_name == "LogisticRegression":
            _explainer = shap.LinearExplainer(model, background)
        else:
            _explainer = shap.TreeExplainer(model)
    return _explainer


def _direction_phrase(feature: str, value: float, shap_val: float) -> str:
    """Turns a SHAP contribution into a plain-English risk driver sentence."""
    name = FRIENDLY_NAMES.get(feature, feature)
    increases = shap_val > 0
    if feature == "credit_score":
        return f"{name} of {int(value)} is {'pushing risk up' if increases else 'pulling risk down'}"
    safe_thresholds = {"debt_to_income_ratio": 0.5, "emi_to_income_ratio": 0.4, "loan_to_income_ratio": 1.0}
    if feature in safe_thresholds:
        above = value > safe_thresholds[feature]
        return f"{name} is {value:.2f} — {'above safe threshold' if above else 'within safe range'}"
    if feature == "previous_defaults" and value > 0:
        return f"{name}: {int(value)} prior default(s) on record"
    if feature == "credit_utilization_score":
        return f"{name} score of {value:.2f} is {'elevated' if increases else 'low'}"
    return f"{name} ({value:.2f}) is {'pushing risk up' if increases else 'pulling risk down'}"


def predict_single(row: dict) -> dict:
    """
    Runs the full scoring pipeline for one borrower:
    financial metrics -> ML default probability -> blended risk score ->
    category -> recommendation -> SHAP explanation.
    """
    bundle = _load_bundle()
    model = bundle["model"]
    scaler = bundle["scaler"]
    model_name = bundle["model_name"]

    X, metrics = build_feature_row(row)
    X = X[FEATURE_COLUMNS]

    if scaler is not None:
        X_scaled = scaler.transform(X)
        default_proba = float(model.predict_proba(X_scaled)[0, 1])
    else:
        default_proba = float(model.predict_proba(X)[0, 1])

    # Blend: 60% ML probability-derived score + 40% rule-based financial score
    ml_score = default_proba * 100
    blended_score = round(0.6 * ml_score + 0.4 * metrics["financial_risk_score"], 2)
    blended_score = float(np.clip(blended_score, 0, 100))

    category = risk_category_from_score(blended_score)
    recommendation = recommendation_from_category(category)

    # ---- SHAP explanation ----
    try:
        import shap
        background = X  # single-row background is fine for TreeExplainer; for Linear we pass zeros
        if model_name == "LogisticRegression":
            background_df = pd.DataFrame(np.zeros((1, len(FEATURE_COLUMNS))), columns=FEATURE_COLUMNS)
            background_scaled = scaler.transform(background_df)
            explainer = _get_explainer(model, model_name, background_scaled)
            shap_values = explainer.shap_values(X_scaled)
            shap_row = shap_values[0]
        else:
            explainer = _get_explainer(model, model_name, X)
            shap_values = explainer.shap_values(X)
            shap_row = shap_values[0] if not isinstance(shap_values, list) else shap_values[1][0]

        contributions = list(zip(FEATURE_COLUMNS, X.iloc[0].values, shap_row))
        contributions.sort(key=lambda t: abs(t[2]), reverse=True)
        top_drivers = [
            _direction_phrase(feat, val, sv) for feat, val, sv in contributions[:4]
        ]
    except Exception:
        # Fallback to rule-based reasoning if SHAP fails for any environment reason
        top_drivers = _fallback_reasons(row, metrics)

    return {
        "model_name": model_name,
        "default_probability": round(default_proba, 4),
        "risk_score": blended_score,
        "risk_category": category,
        "recommendation": recommendation,
        "top_risk_drivers": top_drivers,
        "financial_metrics": metrics,
    }


def _fallback_reasons(row, metrics):
    reasons = []
    if metrics["dti"] > 0.5:
        reasons.append("High Debt-to-Income Ratio")
    if row["credit_score"] < 650:
        reasons.append("Low Credit Score")
    if row.get("previous_defaults", 0) > 0:
        reasons.append("Previous Default History")
    if metrics["eti"] > 0.4:
        reasons.append("High EMI Burden Relative to Income")
    if not reasons:
        reasons.append("Overall financial profile within acceptable limits")
    return reasons


def predict_batch(df: pd.DataFrame) -> pd.DataFrame:
    records = df.to_dict(orient="records")
    results = []
    for r in records:
        try:
            res = predict_single(r)
            results.append(res)
        except Exception as e:
            results.append({
                "model_name": "N/A", "default_probability": None, "risk_score": None,
                "risk_category": "ERROR", "recommendation": "REVIEW",
                "top_risk_drivers": [f"Error: {e}"], "financial_metrics": {}
            })
    out = df.copy().reset_index(drop=True)
    out["default_probability"] = [r["default_probability"] for r in results]
    out["risk_score"] = [r["risk_score"] for r in results]
    out["risk_category"] = [r["risk_category"] for r in results]
    out["recommendation"] = [r["recommendation"] for r in results]
    out["top_risk_drivers"] = [" | ".join(r["top_risk_drivers"]) for r in results]
    return out
