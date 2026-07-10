"""
RiskLens AI - Synthetic Training Data Generator
Generates a realistic, internally-consistent loan book for model training
since no public real bank dataset is bundled. Default risk is simulated
using a logistic latent function over engineered ratios plus noise, so
the resulting relationships mimic real credit risk patterns
(higher DTI/EMI burden & lower credit score => higher default probability).
"""
import numpy as np
import pandas as pd
import os
from src.ml.features import compute_financial_metrics
from src.config import DATA_DIR

RNG = np.random.default_rng(42)


def generate_dataset(n=6000) -> pd.DataFrame:
    employment_types = ["Salaried", "Self-Employed", "Business Owner", "Unemployed", "Retired"]
    purposes = ["Home", "Vehicle", "Education", "Personal", "Business Expansion", "Medical"]

    age = RNG.integers(21, 65, n)
    employment_type = RNG.choice(employment_types, n, p=[0.55, 0.2, 0.15, 0.05, 0.05])
    years_of_employment = np.clip(RNG.normal(7, 5, n), 0, 40)
    annual_income = np.clip(RNG.lognormal(mean=13.2, sigma=0.5, size=n), 150000, 6000000)
    credit_score = np.clip(RNG.normal(680, 90, n), 300, 900).astype(int)
    open_accounts = RNG.integers(0, 12, n)
    previous_defaults = RNG.choice([0, 1, 2, 3], n, p=[0.75, 0.15, 0.07, 0.03])
    loan_amount = np.clip(RNG.lognormal(mean=12.3, sigma=0.7, size=n), 50000, 5000000)
    existing_debt = np.clip(RNG.lognormal(mean=11.5, sigma=0.9, size=n), 0, 3000000)
    monthly_emi = np.clip((loan_amount * 0.03) + RNG.normal(0, 3000, n), 0, None)
    loan_purpose = RNG.choice(purposes, n)

    rows = []
    for i in range(n):
        rows.append({
            "age": int(age[i]),
            "occupation": "N/A",
            "employment_type": employment_type[i],
            "years_of_employment": round(float(years_of_employment[i]), 1),
            "annual_income": round(float(annual_income[i]), 2),
            "loan_amount": round(float(loan_amount[i]), 2),
            "loan_purpose": loan_purpose[i],
            "existing_debt": round(float(existing_debt[i]), 2),
            "monthly_emi": round(float(monthly_emi[i]), 2),
            "credit_score": int(credit_score[i]),
            "open_accounts": int(open_accounts[i]),
            "previous_defaults": int(previous_defaults[i]),
        })

    df = pd.DataFrame(rows)

    # Engineer ratios using the same production logic (single source of truth)
    metrics = df.apply(lambda r: compute_financial_metrics(r.to_dict()), axis=1, result_type="expand")
    df = pd.concat([df, metrics.rename(columns={
        "dti": "debt_to_income_ratio", "eti": "emi_to_income_ratio",
        "lti": "loan_to_income_ratio", "cu_score": "credit_utilization_score"
    })], axis=1)

    # ---- Simulate ground-truth default label via latent logistic function ----
    z = (
        3.2 * df["debt_to_income_ratio"]
        + 2.6 * df["emi_to_income_ratio"]
        + 3.0 * df["credit_utilization_score"]
        + 0.9 * df["previous_defaults"]
        - 0.015 * (df["credit_score"] - 650) / 10
        - 0.05 * df["years_of_employment"]
        - 4.0
    )
    prob_default = 1 / (1 + np.exp(-z))
    noise = RNG.normal(0, 0.05, n)
    prob_default = np.clip(prob_default + noise, 0, 1)
    df["default"] = (RNG.random(n) < prob_default).astype(int)

    return df


if __name__ == "__main__":
    df = generate_dataset()
    out_path = os.path.join(DATA_DIR, "training_dataset.csv")
    df.to_csv(out_path, index=False)
    print(f"Generated {len(df)} rows -> {out_path}")
    print(f"Default rate: {df['default'].mean():.2%}")
