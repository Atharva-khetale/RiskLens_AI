"""
RiskLens AI - Validation Utilities
Ensures data integrity before it ever reaches the database or model,
mirroring the input controls a real loan origination system enforces.
"""

REQUIRED_COLUMNS = [
    "full_name", "age", "occupation", "employment_type", "years_of_employment",
    "annual_income", "loan_amount", "loan_purpose", "existing_debt",
    "monthly_emi", "credit_score", "open_accounts", "previous_defaults",
]


def validate_single_applicant(data: dict) -> list:
    errors = []
    if not data.get("full_name", "").strip():
        errors.append("Full name is required.")
    if not (18 <= data.get("age", 0) <= 100):
        errors.append("Age must be between 18 and 100.")
    if data.get("annual_income", 0) <= 0:
        errors.append("Annual income must be greater than 0.")
    if data.get("loan_amount", 0) <= 0:
        errors.append("Loan amount must be greater than 0.")
    if not (300 <= data.get("credit_score", 0) <= 900):
        errors.append("Credit score must be between 300 and 900.")
    if data.get("existing_debt", 0) < 0:
        errors.append("Existing debt cannot be negative.")
    if data.get("monthly_emi", 0) < 0:
        errors.append("Monthly EMI cannot be negative.")
    if data.get("previous_defaults", 0) < 0:
        errors.append("Previous defaults cannot be negative.")
    return errors


def validate_bulk_dataframe(df) -> list:
    errors = []
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {', '.join(missing_cols)}")
        return errors  # can't validate rows without columns

    if df.empty:
        errors.append("Uploaded file contains no rows.")

    numeric_cols = ["age", "years_of_employment", "annual_income", "loan_amount",
                     "existing_debt", "monthly_emi", "credit_score",
                     "open_accounts", "previous_defaults"]
    for col in numeric_cols:
        if df[col].isnull().any():
            errors.append(f"Column '{col}' has missing values.")

    return errors
