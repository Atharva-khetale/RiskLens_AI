"""
RiskLens AI - Model Performance, Leaderboard & Global Explainability
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json
import pandas as pd
import streamlit as st
import plotly.express as px
from src.config import MODEL_META_PATH

st.set_page_config(page_title="Model Performance | RiskLens AI", page_icon="🧠", layout="wide")
st.title("🧠 Model Performance & Explainability")

if not os.path.exists(MODEL_META_PATH):
    st.warning("No trained model found yet. Train the model first:")
    st.code("python -m src.ml.train")
    st.stop()

with open(MODEL_META_PATH) as f:
    meta = json.load(f)

st.success(f"Best Model Selected: **{meta['best_model']}** (highest ROC-AUC)")

c1, c2, c3 = st.columns(3)
c1.metric("Training Records", meta["n_train"])
c2.metric("Test Records", meta["n_test"])
c3.metric("Historical Default Rate", f"{meta['default_rate']*100:.2f}%")

st.write("---")
st.subheader("🏆 Model Leaderboard")
lb = pd.DataFrame(meta["leaderboard"]).T.reset_index().rename(columns={"index": "model"})
st.dataframe(lb, use_container_width=True)

fig = px.bar(lb, x="model", y=["accuracy", "precision", "recall", "f1_score", "roc_auc"],
             barmode="group", title="Model Comparison — Accuracy / Precision / Recall / F1 / ROC-AUC")
st.plotly_chart(fig, use_container_width=True)

st.write("---")
st.subheader("📖 How RiskLens AI Explains Decisions")
st.markdown("""
For every prediction, RiskLens AI computes **SHAP (SHapley Additive exPlanations) values**
for the trained model. SHAP attributes the model's output for a specific borrower to each
input feature, showing exactly how much each factor (Debt-to-Income Ratio, Credit Score,
Previous Defaults, EMI Burden, etc.) pushed the risk score up or down.

This satisfies a core requirement of model-risk-managed lending: **every automated decision
must be explainable to a credit officer, an auditor, and — where required — the borrower.**

To retrain models on new data:
```bash
python -m src.ml.generate_training_data   # refresh synthetic/real loan book
python -m src.ml.train                    # retrain LR / RF / XGBoost & auto-select best
```
""")
