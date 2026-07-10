# 🏦 RiskLens AI
### AI-Powered Credit Risk & Loan Analytics Platform

🌐 **Live Demo:** https://risklensai-atharvakhetale55.streamlit.app/

RiskLens AI is a full-stack, production-style credit risk assessment platform that
simulates how a bank or NBFC risk team evaluates borrowers, predicts probability of
default (PD), and automates lending decisions — with full explainability and audit
traceability.

Built to demonstrate the intersection of **Data Science, Quantitative Risk, and
FinTech Engineering** for roles such as Risk Analyst, Credit Risk Analyst, Quant
Analyst, Data Analyst, and FinTech Engineer.

---

## 🎥 What It Does

| Capability | Description |
|---|---|
| **Single Applicant Scoring** | Enter one borrower's details and get an instant risk score, default probability, risk category, and lending recommendation. |
| **Bulk Loan Processing** | Upload an Excel file of hundreds of borrowers and score the entire portfolio in one pass. |
| **Explainable AI (XAI)** | Every decision is explained using SHAP values — no black-box lending. |
| **Executive Dashboard** | Approval/rejection rates, risk distribution, monthly trends, credit-score-vs-risk scatter, risk by employment type. |
| **Model Leaderboard** | Logistic Regression vs Random Forest vs XGBoost compared on Accuracy, Precision, Recall, F1, ROC-AUC — best model auto-selected. |
| **PDF Reporting** | Bank-style downloadable PDF reports for both single applicants and full portfolios. |
| **Audit Trail** | Every create/predict/export action is logged to an `audit_logs` table for compliance. |

---

## 🏗️ Architecture

```
┌─────────────────┐      ┌───────────────────┐      ┌─────────────────────┐
│   Streamlit UI    │ ───▶ │   Application Layer │ ───▶ │   MySQL / SQLite DB   │
│ (multipage app)    │      │  (validators, CRUD)  │      │  5 normalized tables  │
└─────────────────┘      └───────────────────┘      └─────────────────────┘
        │                          │
        │                          ▼
        │                ┌───────────────────┐
        │                │  Feature Engineering │
        │                │  (DTI, EMI/Income,    │
        │                │   LTI, Credit Util.)  │
        │                └───────────────────┘
        │                          │
        │                          ▼
        │                ┌───────────────────┐
        └───────────────▶│   ML Scoring Engine   │
                          │ LR / RF / XGBoost      │
                          │  + SHAP Explainer      │
                          └───────────────────┘
                                   │
                                   ▼
                          ┌───────────────────┐
                          │  PDF Report Engine    │
                          │     (fpdf2)            │
                          └───────────────────┘
```

Full details: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

---

## 🧰 Tech Stack

- **Frontend:** Streamlit (multipage app, custom CSS theming)
- **Backend:** Python 3.11+
- **Database:** MySQL (production) / SQLite (zero-config local demo) via SQLAlchemy
- **Data Processing:** Pandas, NumPy
- **Machine Learning:** scikit-learn, XGBoost
- **Explainability:** SHAP
- **Visualization:** Plotly
- **Reporting:** fpdf2 (PDF), openpyxl (Excel)

---

## 📁 Project Structure

```
RiskLens_AI/
├── database/
│   ├── schema.sql              # Production MySQL DDL (5 normalized tables + view)
│   └── seed_data.sql           # Optional demo seed rows
├── src/
│   ├── app.py                  # Streamlit entry point / landing dashboard
│   ├── config.py                # Central configuration (.env driven)
│   ├── pages/
│   │   ├── 1_Single_Applicant.py
│   │   ├── 2_Bulk_Processing.py
│   │   ├── 3_Executive_Dashboard.py
│   │   └── 4_Model_Performance.py
│   ├── db/
│   │   ├── connection.py        # SQLAlchemy engine (MySQL/SQLite)
│   │   └── crud.py              # Data access layer + audit logging
│   ├── ml/
│   │   ├── features.py          # Financial ratio engineering (DTI, EMI/Income...)
│   │   ├── generate_training_data.py  # Realistic synthetic loan-book generator
│   │   ├── train.py             # Trains LR/RF/XGBoost, compares, saves best
│   │   └── predict.py           # Scoring + SHAP explainability engine
│   ├── reports/
│   │   └── pdf_generator.py     # Bank-style PDF report generation
│   └── utils/
│       └── validators.py        # Input validation
├── data/
│   └── sample_loan_applications.xlsx   # Ready-to-use bulk upload demo file
├── models/                      # Trained model artifacts (generated)
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DEPLOYMENT.md
│   ├── RESUME_BULLETS.md
│   └── INTERVIEW_QA.md
├── requirements.txt
└── .env.example
```

---

## 🚀 Quick Start (Local Demo — zero config, SQLite)

```bash
# 1. Clone / unzip the project
cd RiskLens_AI

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment file (defaults to SQLite — no DB setup needed)
cp .env.example .env

# 5. Train the ML models (one-time; trains LR, RF, XGBoost and picks the best)
python -m src.ml.train

# 6. Launch the app
streamlit run src/app.py
```

The app opens at **http://localhost:8501**. Try:
- **Single Applicant Analysis** → fill the form → "Analyze Risk"
- **Bulk Loan Processing** → upload `data/sample_loan_applications.xlsx`
- **Executive Dashboard** → see live analytics update
- **Model Performance** → compare LR / RF / XGBoost leaderboard

---

## 🐬 Running with MySQL (Production Mode)

```bash
# 1. Create the schema
mysql -u root -p < database/schema.sql
mysql -u root -p < database/seed_data.sql   # optional demo rows

# 2. Set environment variables in .env
DB_ENGINE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=risklens_ai

# 3. Run as usual
streamlit run src/app.py
```

Full deployment instructions (Docker, cloud, CI/CD ideas): [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)

---

## 🧠 Machine Learning Approach

1. **Synthetic but realistic training data** is generated (`generate_training_data.py`)
   using a logistic latent-risk function over engineered ratios (DTI, EMI burden,
   credit utilization, previous defaults) — mirroring real-world credit risk drivers
   so the relationships in the data are economically sensible, not random.
2. Three models are trained and benchmarked:
   - Logistic Regression (interpretable baseline)
   - Random Forest (non-linear ensemble)
   - XGBoost (gradient boosting, typically strongest on tabular credit data)
3. **Best model selection** is by **ROC-AUC**, the standard PD-model benchmark used
   in credit risk (insensitive to class threshold, good for imbalanced default rates).
4. **Risk Score (0–100)** blends the ML default probability (60%) with a transparent
   rule-based financial risk score (40%) — so the platform never relies purely on a
   black box, matching real dual-control underwriting practice.
5. **SHAP** explains every individual prediction with the top contributing factors.

> ⚠️ **Note on data:** No proprietary or real bank data is used. Training data is
> synthetically generated with realistic statistical properties for demonstration
> and educational purposes. In production, this pipeline would be retrained on a
> bank's real, anonymized historical loan performance data.

---

## 📊 Database Design

5 normalized tables: `customers`, `loan_applications`, `risk_assessments`,
`predictions`, `audit_logs` — see [`database/schema.sql`](database/schema.sql).

- `customers` (1) → (N) `loan_applications` → (1) `risk_assessments` → (1) `predictions`
- `audit_logs` captures every CREATE / PREDICT / EXPORT action for compliance & model-risk traceability

---

## 📄 Sample Output

```
Risk Score: 84/100
Default Probability: 72%
Risk Category: HIGH RISK
Recommendation: REJECT LOAN

Reasoning:
- High Debt-to-Income Ratio
- Low Credit Score
- Previous Default History
```

---

## 📚 Documentation

- [Architecture Deep-Dive](docs/ARCHITECTURE.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Resume Bullet Points](docs/RESUME_BULLETS.md)
- [Interview Q&A Prep](docs/INTERVIEW_QA.md)

---

## ⚖️ Disclaimer

RiskLens AI is a **portfolio / educational project**. It is not connected to any
real bank, uses synthetic training data, and is not a certified credit scoring
system. It is designed to demonstrate applied data science, risk analytics, and
full-stack engineering skills for lending platforms.
