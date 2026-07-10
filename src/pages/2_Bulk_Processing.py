"""
RiskLens AI - Bulk Loan Processing via Excel Upload
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import io
import pandas as pd
import streamlit as st
import plotly.express as px

from src.utils.validators import validate_bulk_dataframe, REQUIRED_COLUMNS
from src.ml.predict import predict_batch
from src.db.crud import insert_customer, insert_loan_application, insert_risk_assessment, insert_prediction
from src.ml.features import compute_financial_metrics
from src.reports.pdf_generator import generate_portfolio_report

st.set_page_config(page_title="Bulk Processing | RiskLens AI", page_icon="📂", layout="wide")
st.title("📂 Bulk Loan Application Processing")
st.caption("Upload an Excel file of borrowers to score an entire loan book in one pass.")

with st.expander("📋 Required columns & template"):
    st.code(", ".join(REQUIRED_COLUMNS))
    template_df = pd.DataFrame([{
        "full_name": "Ravi Kumar", "age": 34, "occupation": "Engineer",
        "employment_type": "Salaried", "years_of_employment": 8, "annual_income": 1200000,
        "loan_amount": 500000, "loan_purpose": "Home", "existing_debt": 100000,
        "monthly_emi": 15000, "credit_score": 750, "open_accounts": 3, "previous_defaults": 0,
    }])
    buf = io.BytesIO()
    template_df.to_excel(buf, index=False, engine="openpyxl")
    st.download_button("⬇️ Download Excel Template", buf.getvalue(),
                        file_name="loan_applications_template.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

uploaded_file = st.file_uploader("Upload loan_applications.xlsx", type=["xlsx", "xls", "csv"])

if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Could not read file: {e}")
        st.stop()

    errors = validate_bulk_dataframe(df)
    if errors:
        for e in errors:
            st.error(e)
        st.stop()

    st.success(f"Validated {len(df)} records.")
    if st.button("🚀 Run Batch Risk Assessment", use_container_width=True):
        with st.spinner("Scoring portfolio... this may take a moment for large files"):
            scored = predict_batch(df)

            # Persist each record
            progress = st.progress(0)
            for i, row in scored.iterrows():
                rowd = row.to_dict()
                cust_id = insert_customer({k: rowd[k] for k in
                    ["full_name", "age", "occupation", "employment_type", "years_of_employment",
                     "annual_income", "credit_score", "open_accounts", "previous_defaults"]})
                app_id = insert_loan_application({
                    "customer_id": cust_id, "loan_amount": rowd["loan_amount"],
                    "loan_purpose": rowd["loan_purpose"], "existing_debt": rowd["existing_debt"],
                    "monthly_emi": rowd["monthly_emi"],
                })
                fm = compute_financial_metrics(rowd)
                insert_risk_assessment(app_id, {
                    "dti": fm["dti"], "eti": fm["eti"], "lti": fm["lti"],
                    "cu_score": fm["cu_score"], "financial_risk_score": fm["financial_risk_score"],
                })
                insert_prediction(app_id, {
                    "model_name": "batch", "default_probability": rowd["default_probability"],
                    "risk_score": rowd["risk_score"], "risk_category": rowd["risk_category"],
                    "recommendation": rowd["recommendation"],
                    "top_risk_drivers": rowd["top_risk_drivers"].split(" | "),
                })
                progress.progress((i + 1) / len(scored))

        st.session_state["last_scored"] = scored
        st.success("Batch processing complete and saved to database.")

if "last_scored" in st.session_state:
    scored = st.session_state["last_scored"]

    st.write("---")
    st.subheader("📊 Portfolio Risk Summary")
    counts = scored["risk_category"].value_counts()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🟢 Low Risk", int(counts.get("LOW", 0)))
    c2.metric("🟡 Medium Risk", int(counts.get("MEDIUM", 0)))
    c3.metric("🟠 High Risk", int(counts.get("HIGH", 0)))
    c4.metric("🔴 Critical Risk", int(counts.get("CRITICAL", 0)))

    fig = px.pie(names=counts.index, values=counts.values, hole=0.45,
                 color=counts.index,
                 color_discrete_map={"LOW": "#27AE60", "MEDIUM": "#F1C40F", "HIGH": "#E67E22", "CRITICAL": "#C0392B"},
                 title="Risk Category Distribution")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📄 Scored Records")
    st.dataframe(scored, use_container_width=True)

    colA, colB = st.columns(2)
    with colA:
        out_buf = io.BytesIO()
        scored.to_excel(out_buf, index=False, engine="openpyxl")
        st.download_button("⬇️ Download Processed Excel File", out_buf.getvalue(),
                            file_name="processed_loan_applications.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True)
    with colB:
        summary = {
            "Total Applications": len(scored),
            "Approved": int((scored["recommendation"] == "APPROVE").sum()),
            "Rejected": int((scored["recommendation"] == "REJECT").sum()),
            "Avg Risk Score": round(scored["risk_score"].mean(), 2),
        }
        top_risky = scored.sort_values("risk_score", ascending=False).to_dict(orient="records")
        pdf_path = generate_portfolio_report(summary, top_risky)
        with open(pdf_path, "rb") as f:
            st.download_button("⬇️ Download Portfolio Risk Report (PDF)", f,
                                file_name=os.path.basename(pdf_path), mime="application/pdf",
                                use_container_width=True)
