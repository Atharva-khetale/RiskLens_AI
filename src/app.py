"""
RiskLens AI - Main Entry Point (Streamlit multipage app landing screen)
Run with: streamlit run src/app.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from src.db.crud import fetch_summary_view

st.set_page_config(
    page_title="RiskLens AI | Credit Risk Platform",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stApp { background: radial-gradient(circle at top left, #101B34 0%, #0B1220 60%); }
.rl-hero {
    padding: 2.2rem 2.4rem; border-radius: 18px;
    background: linear-gradient(135deg, #0F2A45 0%, #0B3B36 100%);
    border: 1px solid rgba(15,155,142,0.35);
    margin-bottom: 1.4rem;
}
.rl-hero h1 { font-size: 2.3rem; margin-bottom: 0.2rem; color: #F2F7F9;}
.rl-hero p { color: #A9BBD0; font-size: 1.05rem; }
.rl-badge {
    display:inline-block; padding: 3px 12px; border-radius: 999px;
    background: rgba(15,155,142,0.18); color: #35D6BF; font-size:0.78rem;
    font-weight:600; letter-spacing:0.5px; margin-bottom: 0.8rem;
}
.rl-card {
    background: #111C33; border: 1px solid #1E2C4A; border-radius: 14px;
    padding: 1.2rem 1.4rem; height: 100%;
}
.rl-metric-label { color:#8FA2BE; font-size:0.85rem; text-transform:uppercase; letter-spacing:0.5px;}
.rl-metric-value { color:#F2F7F9; font-size:1.9rem; font-weight:700; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.markdown("""
<div class="rl-hero">
  <div class="rl-badge">AI-POWERED CREDIT RISK ENGINE</div>
  <h1>RiskLens AI</h1>
  <p>Loan default prediction, borrower risk scoring, and explainable lending
  decisions for banks, NBFCs, and FinTech lenders.</p>
</div>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
try:
    data = fetch_summary_view()
except Exception:
    data = []

total_apps = len(data)
approved = sum(1 for d in data if d.get("recommendation") == "APPROVE")
rejected = sum(1 for d in data if d.get("recommendation") == "REJECT")
avg_score = round(sum(d.get("risk_score") or 0 for d in data) / total_apps, 1) if total_apps else 0

for col, label, value in zip(
    [col1, col2, col3, col4],
    ["Total Applications", "Approved", "Rejected", "Avg Risk Score"],
    [total_apps, approved, rejected, avg_score],
):
    with col:
        st.markdown(f"""
        <div class="rl-card">
            <div class="rl-metric-label">{label}</div>
            <div class="rl-metric-value">{value}</div>
        </div>
        """, unsafe_allow_html=True)

st.write("")
st.subheader("Navigate")

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.page_link("pages/1_Single_Applicant.py", label="👤 Single Applicant Analysis", use_container_width=True)
with c2:
    st.page_link("pages/2_Bulk_Processing.py", label="📂 Bulk Loan Processing", use_container_width=True)
with c3:
    st.page_link("pages/3_Executive_Dashboard.py", label="📊 Executive Dashboard", use_container_width=True)
with c4:
    st.page_link("pages/4_Model_Performance.py", label="🧠 Model Performance & XAI", use_container_width=True)

st.write("---")
st.markdown("""
##### About RiskLens AI
RiskLens AI simulates an end-to-end institutional lending risk workflow:

1. **Ingest** — single-applicant forms or bulk Excel uploads
2. **Store** — normalized relational schema (customers, applications, risk assessments, predictions, audit logs)
3. **Score** — rule-based financial ratios blended with an XGBoost/Random Forest/Logistic Regression
   probability-of-default model (best model auto-selected by ROC-AUC)
4. **Explain** — SHAP-based reasoning for every decision
5. **Decide** — Approve / Review / Reject recommendation with full audit trail
6. **Report** — downloadable PDF risk reports and portfolio dashboards

Built with Streamlit, scikit-learn, XGBoost, SHAP, Plotly, and MySQL.
""")
