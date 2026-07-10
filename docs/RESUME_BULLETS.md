# RiskLens AI — Resume Bullet Points

Pick 3–5 that best match the role you're applying for. Quantify further with your
own numbers if you extend the project (e.g., actual dataset size you tested on).

## General / Data Analyst Framing
- Designed and built **RiskLens AI**, a full-stack credit risk analytics platform
  that ingests borrower data via web forms and bulk Excel uploads, computes
  underwriting ratios (DTI, EMI-to-Income, LTI), and stores results in a
  normalized 5-table relational schema (MySQL/SQLAlchemy).
- Built interactive **Plotly/Streamlit dashboards** surfacing approval rate,
  rejection rate, risk distribution, monthly application trends, and risk-by-
  segment analytics for portfolio-level decision-making.
- Automated bulk risk processing for entire loan books via Excel upload,
  producing scored Excel exports and bank-style PDF portfolio reports in a
  single workflow.

## Data Scientist / ML Framing
- Trained and benchmarked **Logistic Regression, Random Forest, and XGBoost**
  models to predict probability of default, comparing Accuracy, Precision,
  Recall, F1, and ROC-AUC, with automatic best-model selection by ROC-AUC
  (the industry-standard PD-model benchmark).
- Implemented **SHAP-based explainable AI** so every automated lending decision
  ships with a plain-English, feature-level justification (e.g., high DTI, low
  credit score, prior defaults) — aligned with fair-lending/model-risk-management
  practices.
- Engineered a **blended risk-scoring methodology** combining a transparent
  rule-based financial risk score (40%) with ML-derived default probability
  (60%) to avoid pure black-box lending decisions.
- Generated a statistically realistic synthetic loan-book dataset with a
  logistic latent-risk simulation to train and validate PD models in the
  absence of proprietary bank data.

## FinTech / Risk Analyst Framing
- Simulated an end-to-end **institutional lending risk workflow** — application
  intake, financial ratio computation, automated Approve/Review/Reject
  recommendations, and full audit-log traceability — mirroring real bank/NBFC
  credit risk operations.
- Classified borrowers into **Low / Medium / High / Critical risk tiers** using
  a configurable risk-banding framework, driving automated lending
  recommendations consistent with underwriting policy thresholds.
- Designed a normalized SQL schema (`customers`, `loan_applications`,
  `risk_assessments`, `predictions`, `audit_logs`) supporting compliance-grade
  traceability of every credit decision.

## Full-Stack / Engineering Framing
- Built a production-style **Streamlit multipage application** with a custom
  banking-style UI theme, environment-driven configuration (SQLite for
  local/demo, MySQL for production), and modular architecture (validators,
  data access layer, ML pipeline, PDF reporting engine) cleanly separated for
  testability and maintainability.
- Implemented a database-agnostic data access layer using **SQLAlchemy**,
  enabling zero-code-change portability between SQLite (development) and MySQL
  (production).
- Authored bank-style downloadable **PDF report generation** (fpdf2) for both
  individual applicant risk reports and portfolio-wide summary reports.
