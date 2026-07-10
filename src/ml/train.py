"""
RiskLens AI - Model Training Pipeline
Trains Logistic Regression, Random Forest, and XGBoost classifiers to
predict probability of default (PD). Compares Accuracy, Precision,
Recall, F1 and ROC-AUC, then persists the best-performing model
(by ROC-AUC, the standard credit-risk benchmark metric) along with
metadata for the Streamlit app to consume.
"""
import os
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                              f1_score, roc_auc_score, confusion_matrix)
from xgboost import XGBClassifier

from src.ml.features import FEATURE_COLUMNS
from src.config import DATA_DIR, BEST_MODEL_PATH, MODEL_META_PATH


def load_training_data() -> pd.DataFrame:
    path = os.path.join(DATA_DIR, "training_dataset.csv")
    if not os.path.exists(path):
        from src.ml.generate_training_data import generate_dataset
        df = generate_dataset()
        df.to_csv(path, index=False)
    return pd.read_csv(path)


def train_all_models():
    df = load_training_data()
    X = df[FEATURE_COLUMNS]
    y = df["default"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    models = {
        "LogisticRegression": LogisticRegression(max_iter=1000, class_weight="balanced"),
        "RandomForest": RandomForestClassifier(
            n_estimators=300, max_depth=8, class_weight="balanced", random_state=42, n_jobs=-1
        ),
        "XGBoost": XGBClassifier(
            n_estimators=300, max_depth=5, learning_rate=0.05,
            subsample=0.9, colsample_bytree=0.9, eval_metric="logloss",
            random_state=42, n_jobs=-1
        ),
    }

    results = {}
    fitted = {}

    for name, model in models.items():
        if name == "LogisticRegression":
            model.fit(X_train_scaled, y_train)
            y_pred = model.predict(X_test_scaled)
            y_proba = model.predict_proba(X_test_scaled)[:, 1]
        else:
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            y_proba = model.predict_proba(X_test)[:, 1]

        results[name] = {
            "accuracy": round(accuracy_score(y_test, y_pred), 4),
            "precision": round(precision_score(y_test, y_pred), 4),
            "recall": round(recall_score(y_test, y_pred), 4),
            "f1_score": round(f1_score(y_test, y_pred), 4),
            "roc_auc": round(roc_auc_score(y_test, y_proba), 4),
        }
        fitted[name] = model

    # Select best model by ROC-AUC (industry-standard PD model benchmark)
    best_name = max(results, key=lambda k: results[k]["roc_auc"])
    best_model = fitted[best_name]

    bundle = {
        "model": best_model,
        "scaler": scaler if best_name == "LogisticRegression" else None,
        "model_name": best_name,
        "feature_columns": FEATURE_COLUMNS,
    }
    joblib.dump(bundle, BEST_MODEL_PATH)

    meta = {
        "best_model": best_name,
        "leaderboard": results,
        "n_train": len(X_train),
        "n_test": len(X_test),
        "default_rate": round(float(y.mean()), 4),
    }
    with open(MODEL_META_PATH, "w") as f:
        json.dump(meta, f, indent=2)

    return meta


if __name__ == "__main__":
    meta = train_all_models()
    print(json.dumps(meta, indent=2))
