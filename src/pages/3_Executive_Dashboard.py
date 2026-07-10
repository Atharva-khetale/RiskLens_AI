"""
RiskLens AI - Executive Risk Dashboard
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd
import streamlit as st
import plotly.express as px
from src.db.crud import fetch_summary_view

st.set_page_config(page_title="Dashboard | RiskLens AI", page_icon="📊", layout="wide")
st.title("📊 Executive Risk Dashboard")
st.caption("Portfolio-level view across all applications processed by RiskLens AI.")

data = fetch_summary_view()
if not data:
    st.info("No applications yet. Run a Single Applicant analysis or Bulk upload first.")
    st.stop()

df = pd.DataFrame(data)
df["application_date"] = pd.to_datetime(df["application_date"])

total = len(df)
approved = (df["recommendation"] == "APPROVE").sum()
reviewed = (df["recommendation"] == "REVIEW").sum()
rejected = (df["recommendation"] == "REJECT").sum()
avg_score = round(df["risk_score"].mean(), 1)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Applications", total)
c2.metric("Approval Rate", f"{approved/total*100:.1f}%")
c3.metric("Review Rate", f"{reviewed/total*100:.1f}%")
c4.metric("Rejection Rate", f"{rejected/total*100:.1f}%")
c5.metric("Avg Risk Score", avg_score)

st.write("---")
col1, col2 = st.columns(2)
with col1:
    cat_counts = df["risk_category"].value_counts()
    fig1 = px.bar(x=cat_counts.index, y=cat_counts.values,
                  labels={"x": "Risk Category", "y": "Count"},
                  color=cat_counts.index,
                  color_discrete_map={"LOW": "#27AE60", "MEDIUM": "#F1C40F", "HIGH": "#E67E22", "CRITICAL": "#C0392B"},
                  title="Risk Distribution")
    st.plotly_chart(fig1, use_container_width=True)
with col2:
    rec_counts = df["recommendation"].value_counts()
    fig2 = px.pie(names=rec_counts.index, values=rec_counts.values, hole=0.45,
                  title="Lending Decisions")
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("📈 Monthly Application Trend")
monthly = df.set_index("application_date").resample("ME").size().reset_index(name="applications")
fig3 = px.line(monthly, x="application_date", y="applications", markers=True,
               title="Applications Over Time")
st.plotly_chart(fig3, use_container_width=True)

st.subheader("💳 Credit Score vs Risk Score")
fig4 = px.scatter(df, x="credit_score", y="risk_score", color="risk_category",
                   size="loan_amount", hover_data=["full_name"],
                   color_discrete_map={"LOW": "#27AE60", "MEDIUM": "#F1C40F", "HIGH": "#E67E22", "CRITICAL": "#C0392B"},
                   title="Credit Score vs Model Risk Score")
st.plotly_chart(fig4, use_container_width=True)

st.subheader("🏢 Risk by Employment Type")
emp_risk = df.groupby("employment_type")["risk_score"].mean().sort_values(ascending=False).reset_index()
fig5 = px.bar(emp_risk, x="employment_type", y="risk_score", title="Average Risk Score by Employment Type")
st.plotly_chart(fig5, use_container_width=True)

st.subheader("📋 Full Application Log")
st.dataframe(df.sort_values("application_date", ascending=False), use_container_width=True)
