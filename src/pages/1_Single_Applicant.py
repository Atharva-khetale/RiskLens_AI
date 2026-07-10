"""
RiskLens AI - Single Applicant Analysis
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
from src.utils.validators import validate_single_applicant
from src.ml.predict import predict_single
from src.db.crud import insert_customer, insert_loan_application, insert_risk_assessment, insert_prediction
from src.reports.pdf_generator import generate_single_report

st.set_page_config(page_title="Single Applicant | RiskLens AI", page_icon="👤", layout="wide")
st.title("👤 Single Applicant Risk Analysis")
st.caption("Enter borrower details to run a full credit risk assessment in real time.")

with st.form("applicant_form"):
    c1, c2, c3 = st.columns(3)
    with c1:
        full_name = st.text_input("Full Name*")
        age = st.number_input("Age*", min_value=18, max_value=100, value=30)
        occupation = st.text_input("Occupation", value="Salaried Professional")
        employment_type = st.selectbox("Employment Type*",
            ["Salaried", "Self-Employed", "Business Owner", "Unemployed", "Retired"])
    with c2:
        years_of_employment = st.number_input("Years of Employment", min_value=0.0, max_value=45.0, value=3.0, step=0.5)
        annual_income = st.number_input("Annual Income (₹)*", min_value=0.0, value=800000.0, step=10000.0)
        loan_amount = st.number_input("Loan Amount (₹)*", min_value=0.0, value=500000.0, step=10000.0)
        loan_purpose = st.selectbox("Loan Purpose",
            ["Home", "Vehicle", "Education", "Personal", "Business Expansion", "Medical"])
    with c3:
        existing_debt = st.number_input("Existing Debt (₹)", min_value=0.0, value=100000.0, step=5000.0)
        monthly_emi = st.number_input("Monthly EMI (₹)", min_value=0.0, value=15000.0, step=1000.0)
        credit_score = st.number_input("Credit Score*", min_value=300, max_value=900, value=700)
        open_accounts = st.number_input("Number of Open Accounts", min_value=0, max_value=30, value=2)
        previous_defaults = st.number_input("Previous Defaults", min_value=0, max_value=10, value=0)

    submitted = st.form_submit_button("🔍 Analyze Risk", use_container_width=True)

if submitted:
    applicant = dict(
        full_name=full_name, age=age, occupation=occupation, employment_type=employment_type,
        years_of_employment=years_of_employment, annual_income=annual_income, loan_amount=loan_amount,
        loan_purpose=loan_purpose, existing_debt=existing_debt, monthly_emi=monthly_emi,
        credit_score=credit_score, open_accounts=open_accounts, previous_defaults=previous_defaults,
    )
    errors = validate_single_applicant(applicant)
    if errors:
        for e in errors:
            st.error(e)
    else:
        with st.spinner("Running risk model..."):
            result = predict_single(applicant)

            # Persist to DB
            cust_id = insert_customer({k: applicant[k] for k in
                ["full_name", "age", "occupation", "employment_type", "years_of_employment",
                 "annual_income", "credit_score", "open_accounts", "previous_defaults"]})
            app_id = insert_loan_application({
                "customer_id": cust_id, "loan_amount": loan_amount, "loan_purpose": loan_purpose,
                "existing_debt": existing_debt, "monthly_emi": monthly_emi,
            })
            fm = result["financial_metrics"]
            insert_risk_assessment(app_id, {
                "dti": fm["dti"], "eti": fm["eti"], "lti": fm["lti"],
                "cu_score": fm["cu_score"], "financial_risk_score": fm["financial_risk_score"],
            })
            insert_prediction(app_id, result)

        st.success("Assessment complete and saved to database.")

        cat = result["risk_category"]
        color_map = {"LOW": "#27AE60", "MEDIUM": "#F1C40F", "HIGH": "#E67E22", "CRITICAL": "#C0392B"}
        rec_color = "#27AE60" if result["recommendation"] == "APPROVE" else ("#F1C40F" if result["recommendation"] == "REVIEW" else "#C0392B")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Risk Score", f"{result['risk_score']}/100")
        m2.metric("Default Probability", f"{result['default_probability']*100:.1f}%")
        m3.markdown(f"**Risk Category**<br><span style='color:{color_map[cat]};font-size:1.4rem;font-weight:700'>{cat} RISK</span>", unsafe_allow_html=True)
        m4.markdown(f"**Recommendation**<br><span style='color:{rec_color};font-size:1.4rem;font-weight:700'>{result['recommendation']} LOAN</span>", unsafe_allow_html=True)

        st.write("---")
        st.subheader("🧠 Why this decision? (Explainable AI)")
        for reason in result["top_risk_drivers"]:
            st.markdown(f"- {reason}")

        st.write("---")
        st.subheader("📐 Financial Ratios")
        r1, r2, r3, r4, r5 = st.columns(5)
        r1.metric("Debt-to-Income", fm["dti"])
        r2.metric("EMI-to-Income", fm["eti"])
        r3.metric("Loan-to-Income", fm["lti"])
        r4.metric("Credit Utilization", fm["cu_score"])
        r5.metric("Rule-Based Score", fm["financial_risk_score"])

        pdf_path = generate_single_report(applicant, result)
        with open(pdf_path, "rb") as f:
            st.download_button("⬇️ Download Full PDF Report", f, file_name=os.path.basename(pdf_path),
                                mime="application/pdf", use_container_width=True)
