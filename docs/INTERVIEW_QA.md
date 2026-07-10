# RiskLens AI — Interview Questions & Answers

Organized by theme. Use these as talking points — adapt to your own voice, and be
ready to open the code and walk through it live.

---

## A. Project Overview & Motivation

**Q: Walk me through RiskLens AI in 60 seconds.**
A: It's an end-to-end credit risk platform. A lender enters a borrower's details
(or uploads a batch via Excel), the system computes standard underwriting ratios
like debt-to-income, runs a trained ML model to estimate probability of default,
blends that with a transparent rule-based score, classifies the borrower into a
risk tier, and returns an Approve/Review/Reject recommendation with a SHAP-based
explanation. Everything is persisted in a normalized SQL schema with full audit
logging, and results can be exported as PDF reports.

**Q: Why did you build this?**
A: To demonstrate the full skill stack a bank/FinTech risk role needs: financial
domain knowledge (ratios, risk banding), applied ML (model comparison, PD
estimation), explainability (SHAP, which is table stakes in regulated lending),
and engineering (schema design, a working app, deployment story) — rather than
just a notebook with a model.

---

## B. Data & Modeling

**Q: What data did you train on? Isn't synthetic data a limitation?**
A: Yes — I don't have access to proprietary bank loan performance data, so I
built a synthetic generator that samples realistic distributions for income,
credit score, employment, etc., and simulates defaults via a logistic latent-risk
function driven by the same ratios (DTI, EMI burden, credit utilization,
previous defaults) that actually drive real-world defaults. This keeps the
statistical relationships economically sensible rather than random, so the
model-comparison exercise (LR vs RF vs XGBoost) and the SHAP explanations are
meaningful. In production, this exact pipeline would be retrained on the
institution's real, anonymized historical loan book.

**Q: Why compare three models instead of just using XGBoost?**
A: Different models trade off interpretability vs. predictive power differently.
Logistic Regression gives a fully linear, auditable baseline (some regulators
prefer this for transparency). Random Forest and XGBoost typically capture
non-linear interactions better. I benchmark all three on Accuracy, Precision,
Recall, F1, and ROC-AUC and auto-select the best by ROC-AUC, since that's the
threshold-independent metric standard for PD models. It also makes the
"Model Performance" dashboard a genuine leaderboard, not a foregone conclusion.

**Q: Why ROC-AUC as the selection metric specifically?**
A: Default rates are often imbalanced, and business teams later choose their own
approval threshold based on risk appetite. ROC-AUC measures ranking quality
across all thresholds, which is what you want when the operating threshold isn't
fixed yet — versus accuracy, which is threshold-dependent and misleading under
class imbalance.

**Q: How do you handle class imbalance?**
A: `class_weight="balanced"` for Logistic Regression and Random Forest so the
minority (default) class isn't ignored; XGBoost's boosting objective already
tends to handle moderate imbalance reasonably, though `scale_pos_weight` is a
natural next tuning step if the real default rate is far more skewed than my
synthetic ~20-45% range.

**Q: What's the difference between the "Financial Risk Score" and the ML "Risk
Score"?**
A: The Financial Risk Score is a fully deterministic, rule-based 0-100 score
computed directly from ratios like DTI and EMI burden — auditable, no ML
involved. The final Risk Score blends the ML model's default probability (60%)
with this rule-based score (40%). This dual-control approach reflects how real
credit committees work: they don't let a model decide unilaterally.

---

## C. Explainability

**Q: Why SHAP instead of just feature importances?**
A: Global feature importance tells you what matters on average across the whole
model; SHAP gives a *per-prediction* explanation — exactly why *this* borrower
got *this* score. In lending, individual-level explainability is often a
regulatory/fair-lending expectation (adverse action reasons), not just a nice
UX feature.

**Q: How does SHAP work at a high level?**
A: It's grounded in cooperative game theory (Shapley values) — it fairly
attributes a model's output for one prediction to each input feature by
averaging that feature's marginal contribution across all possible feature
orderings/coalitions. For tree models I use `TreeExplainer` (efficient, exact for
trees); for Logistic Regression I use `LinearExplainer` (exact for linear
models given feature covariance).

---

## D. Database & Engineering

**Q: Why this specific schema — why separate `risk_assessments` from
`predictions`?**
A: To keep the deterministic rule-based metrics independently auditable from the
ML model's output. If a regulator or internal model-risk team wants to know "what
did the rules say" vs. "what did the model say" they're two separate, queryable
records rather than conflated fields.

**Q: Why SQLite for dev and MySQL for prod — doesn't that risk behavioral
drift?**
A: The data access layer goes through SQLAlchemy with portable SQL (no
MySQL-specific syntax in the app code), so the risk is low, and it buys a
zero-friction local/demo experience. In a real production hardening pass, I'd
add a CI step running the test suite against a real MySQL container to catch any
drift before it reaches production.

**Q: How would this scale to millions of applications?**
A: Move bulk scoring off the Streamlit thread into an async worker/queue
(Celery/RQ or a scheduled batch job), paginate the dashboard queries instead of
loading the full joined view, add indexes on `risk_category` and
`application_status` (already present), and consider a read-replica for
dashboard queries separate from the write path used for scoring.

---

## E. Risk / Domain Questions

**Q: What is Debt-to-Income ratio and why does it matter?**
A: (existing debt + new loan amount) / annual income. It's one of the most
fundamental underwriting ratios — it estimates how much of a borrower's income is
already or would be committed to debt obligations, directly related to
repayment capacity. Most lenders cap it around 40-50%.

**Q: How would you validate this model before deploying it to real lending
decisions?**
A: Back-test on a real historical hold-out with known outcomes, check
calibration (predicted PD vs actual observed default rate by decile), monitor
for population stability (PSI) between training and live population, run fair-
lending/disparate-impact analysis across protected classes, and require
human-in-the-loop review for the "REVIEW" tier and any edge cases before full
automation.

**Q: What are the limitations of this project as-is?**
A: Synthetic training data (not a real bank's loan performance history), no
macroeconomic/vintage effects modeled, no formal model validation/backtesting
framework, and the risk-banding thresholds are illustrative rather than
calibrated to a specific institution's risk appetite. I'd flag all of these
explicitly to any hiring team as "next steps," which shows I understand the gap
between a portfolio project and a production credit model.

---

## F. Behavioral / Follow-up

**Q: What would you build next?**
A: A backtesting/monitoring module (PSI/CSI drift charts over time), a
champion/challenger model comparison workflow, calibration curves per risk band,
and role-based access control so "REVIEW" tier applications route to a human
underwriter queue inside the app itself.
