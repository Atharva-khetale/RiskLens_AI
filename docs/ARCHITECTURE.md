# RiskLens AI — Architecture Deep Dive

## 1. Design Principles

1. **Separation of concerns** — UI (Streamlit pages), business logic (validators,
   feature engineering), data access (CRUD layer), and ML (train/predict) are
   independent modules. The UI never talks to the database directly.
2. **Dual-control risk scoring** — the final Risk Score blends a transparent,
   auditable rule-based score with an ML-derived probability of default, mirroring
   how real risk committees don't fully delegate credit decisions to a black box.
3. **Explainability by default** — every prediction carries a SHAP-derived reason
   set; nothing is approved/rejected without a stated reason, as required by
   fair-lending and model-risk-management practices (e.g., SR 11-7 style governance).
4. **Environment portability** — SQLite for zero-friction local demos and
   interviews, MySQL for a production-representative deployment, switched purely
   via `.env`.

## 2. Data Flow

```
User Input (form or Excel)
        │
        ▼
Validators (utils/validators.py)  ── reject malformed/missing data early
        │
        ▼
Feature Engineering (ml/features.py)
   - Debt-to-Income Ratio
   - EMI-to-Income Ratio
   - Loan-to-Income Ratio
   - Credit Utilization Score
   - Rule-based Financial Risk Score (0-100, fully transparent formula)
        │
        ▼
ML Scoring (ml/predict.py)
   - Loads best model (auto-selected at training time by ROC-AUC)
   - Computes default probability
   - Blends with rule-based score → final Risk Score (0-100)
   - Maps score → Risk Category (LOW / MEDIUM / HIGH / CRITICAL)
   - Maps category → Recommendation (APPROVE / REVIEW / REJECT)
   - SHAP explains top contributing features
        │
        ▼
Persistence (db/crud.py)
   customers → loan_applications → risk_assessments → predictions
   every write also appends to audit_logs
        │
        ▼
Reporting (reports/pdf_generator.py)
   - Single applicant PDF
   - Portfolio-level PDF
        │
        ▼
Dashboard (pages/3_Executive_Dashboard.py)
   - Reads the joined summary view for live analytics
```

## 3. Why These Specific Financial Ratios?

| Ratio | Formula | Why it matters to lenders |
|---|---|---|
| Debt-to-Income (DTI) | (existing_debt + loan_amount) / annual_income | Core underwriting metric; most regulators/banks cap DTI (commonly ~40-50%) |
| EMI-to-Income (EMI burden) | monthly_emi / monthly_income | Measures repayment capacity strain in the near term |
| Loan-to-Income (LTI) | loan_amount / annual_income | Sizes the loan relative to earning capacity |
| Credit Utilization Score | function of credit score + open accounts | Proxy for existing credit stress/over-leverage |

## 4. Model Selection Logic

Three candidate models are trained on identical train/test splits:

- **Logistic Regression** — interpretable baseline, fast, good linear signal capture
- **Random Forest** — captures non-linear interactions, robust to outliers
- **XGBoost** — typically strongest on structured/tabular financial data

The model with the **highest ROC-AUC** on the held-out test set is automatically
selected and persisted (`models/best_model.joblib`), because ROC-AUC is
threshold-independent and the standard benchmark for probability-of-default (PD)
models in credit risk.

## 5. Explainability (SHAP)

- Tree-based models (RF, XGBoost) use `shap.TreeExplainer`.
- Logistic Regression uses `shap.LinearExplainer`.
- For every prediction, the top 4 features by |SHAP value| are converted into
  plain-English statements (e.g., *"Debt-to-Income Ratio is 0.62 — above safe
  threshold"*) and stored alongside the prediction (`predictions.top_risk_drivers`,
  JSON column) for full auditability.

## 6. Database Schema Rationale (3NF)

- `customers` holds KYC-level, relatively static borrower attributes.
- `loan_applications` is a 1:N child of `customers` — a person can apply multiple
  times.
- `risk_assessments` isolates the deterministic, rule-based metrics from the
- `predictions` table, which isolates the ML model output — this separation lets
  you audit "what the rules said" vs "what the model said" independently, which
  real model-risk-management frameworks require.
- `audit_logs` is intentionally denormalized (JSON `details` column) since audit
  trails need to capture arbitrary, evolving payloads without schema migrations.

## 7. Scalability Notes

- The CRUD layer is written against SQLAlchemy Core, so swapping SQLite → MySQL →
  PostgreSQL requires only a connection string change.
- Bulk scoring is vectorization-friendly; `predict_batch` can be parallelized
  with multiprocessing or moved to a batch job (e.g., Airflow DAG / Celery task)
  for very large loan books without changing the scoring logic itself.
- SHAP explanation cost is the main latency driver for bulk jobs; for production
  at scale, this would run asynchronously with results cached back to
  `predictions.top_risk_drivers`.
