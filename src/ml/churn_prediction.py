"""
src/ml/churn_prediction.py
----------------------------
Machine Learning Module 1: Customer Churn Prediction.

Defines churn at the customer level (Recency > CHURN_RECENCY_THRESHOLD_DAYS
days since last purchase, relative to the dataset's snapshot date — i.e. a
customer who has gone quiet for 90+ days) and trains a binary classifier to
predict it from behavioral features available *before* the churn window
(Frequency, Monetary, AOV, tenure, category mix, discount sensitivity, etc.)

Models compared:
    - Logistic Regression (interpretable baseline)
    - Random Forest Classifier
    - XGBoost Classifier (final/production model)

Evaluation:
    - Train/test split (stratified, 80/20)
    - Accuracy, Precision, Recall, F1, ROC-AUC
    - Confusion matrix
    - Feature importance (XGBoost gain-based)

Run:
    python -m src.ml.churn_prediction
"""

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from src import config
from src.utils import get_logger, load_csv, save_csv, save_fig, setup_plot_style

logger = get_logger(__name__)

try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False


def build_feature_table() -> pd.DataFrame:
    """Join transactional, RFM, and CLV data into one customer-level feature table."""
    df = load_csv(config.FEATURED_SALES_FILE, parse_dates=["Order_Date", "Ship_Date"])
    rfm = load_csv(config.RFM_FILE)
    clv = load_csv(config.CLV_FILE)

    # Behavioral / mix features from the transactional table
    cust = df.groupby("Customer_ID").agg(
        Avg_Discount=("Discount", "mean"),
        Avg_Delivery_Days=("Delivery_Days", "mean"),
        Avg_Profit_Margin=("Profit_Margin", "mean"),
        Distinct_Categories=("Product_Category", "nunique"),
        Weekend_Order_Share=("Is_Weekend", "mean"),
        Total_Quantity=("Quantity", "sum"),
        Segment=("Segment", "first"),
        Region=("Region", "first"),
    ).reset_index()

    features = (
        rfm[["Customer_ID", "Recency", "Frequency", "Monetary", "RFM_Score_Numeric"]]
        .merge(clv[["Customer_ID", "Avg_Order_Value", "Purchase_Frequency",
                     "Lifespan_Days", "Gross_Margin_Pct"]], on="Customer_ID", how="left")
        .merge(cust, on="Customer_ID", how="left")
    )

    # Target: churned if Recency exceeds the business threshold
    features["Churned"] = (features["Recency"] > config.CHURN_RECENCY_THRESHOLD_DAYS).astype(int)
    return features


def prepare_xy(features: pd.DataFrame):
    feature_cols = [
        "Frequency", "Monetary", "RFM_Score_Numeric", "Avg_Order_Value",
        "Purchase_Frequency", "Lifespan_Days", "Gross_Margin_Pct",
        "Avg_Discount", "Avg_Delivery_Days", "Avg_Profit_Margin",
        "Distinct_Categories", "Weekend_Order_Share", "Total_Quantity",
    ]
    X = pd.get_dummies(
        features[feature_cols + ["Segment", "Region"]], columns=["Segment", "Region"], drop_first=True
    )
    y = features["Churned"]
    return X, y, X.columns.tolist()


def train_models(X_train, X_test, y_train, y_test):
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    models = {
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=config.RANDOM_STATE),
        "Random Forest": RandomForestClassifier(
            n_estimators=200, max_depth=6, random_state=config.RANDOM_STATE
        ),
    }
    if XGBOOST_AVAILABLE:
        models["XGBoost"] = XGBClassifier(
            n_estimators=200, max_depth=4, learning_rate=0.05,
            subsample=0.9, colsample_bytree=0.9, eval_metric="logloss",
            random_state=config.RANDOM_STATE,
        )

    results = []
    fitted = {}
    for name, model in models.items():
        if name == "Logistic Regression":
            model.fit(X_train_scaled, y_train)
            preds = model.predict(X_test_scaled)
            proba = model.predict_proba(X_test_scaled)[:, 1]
        else:
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            proba = model.predict_proba(X_test)[:, 1]

        results.append({
            "Model": name,
            "Accuracy": accuracy_score(y_test, preds),
            "Precision": precision_score(y_test, preds, zero_division=0),
            "Recall": recall_score(y_test, preds, zero_division=0),
            "F1_Score": f1_score(y_test, preds, zero_division=0),
            "ROC_AUC": roc_auc_score(y_test, proba),
        })
        fitted[name] = {"model": model, "preds": preds, "proba": proba}

    results_df = pd.DataFrame(results).sort_values("ROC_AUC", ascending=False)
    return results_df, fitted, scaler


def plot_confusion_and_roc(y_test, fitted: dict, best_model_name: str):
    setup_plot_style()
    preds = fitted[best_model_name]["preds"]
    proba = fitted[best_model_name]["proba"]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    cm = confusion_matrix(y_test, preds)
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=axes[0],
                xticklabels=["Active", "Churned"], yticklabels=["Active", "Churned"])
    axes[0].set_title(f"Confusion Matrix — {best_model_name}")
    axes[0].set_xlabel("Predicted")
    axes[0].set_ylabel("Actual")

    fpr, tpr, _ = roc_curve(y_test, proba)
    auc = roc_auc_score(y_test, proba)
    axes[1].plot(fpr, tpr, color="#2563eb", label=f"AUC = {auc:.3f}")
    axes[1].plot([0, 1], [0, 1], "--", color="gray")
    axes[1].set_title("ROC Curve")
    axes[1].set_xlabel("False Positive Rate")
    axes[1].set_ylabel("True Positive Rate")
    axes[1].legend()

    fig.suptitle("Customer Churn Prediction — Model Evaluation", fontsize=15, fontweight="bold")
    fig.tight_layout()
    save_fig(fig, "29_churn_model_evaluation.png")


def plot_feature_importance(model, feature_names, model_name: str):
    setup_plot_style()
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
    else:
        return

    imp_df = pd.DataFrame({"Feature": feature_names, "Importance": importances})
    imp_df = imp_df.sort_values("Importance", ascending=False).head(12)

    fig, ax = plt.subplots(figsize=(9, 7))
    sns.barplot(data=imp_df, x="Importance", y="Feature", hue="Feature", legend=False,
                palette="viridis", ax=ax)
    ax.set_title(f"Top Feature Importances — {model_name} (Churn Model)", fontweight="bold")
    fig.tight_layout()
    save_fig(fig, "30_churn_feature_importance.png")
    return imp_df


def run():
    features = build_feature_table()
    logger.info("Churn rate in feature table: %.2f%%", features["Churned"].mean() * 100)

    X, y, feature_names = prepare_xy(features)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=config.RANDOM_STATE, stratify=y
    )

    results_df, fitted, scaler = train_models(X_train, X_test, y_train, y_test)
    logger.info("Model comparison:\n%s", results_df.to_string(index=False))

    best_model_name = results_df.iloc[0]["Model"]
    best_model = fitted[best_model_name]["model"]
    logger.info("Best model by ROC-AUC: %s", best_model_name)

    plot_confusion_and_roc(y_test, fitted, best_model_name)
    imp_df = plot_feature_importance(best_model, feature_names, best_model_name)

    logger.info("\n%s", classification_report(y_test, fitted[best_model_name]["preds"]))

    save_csv(results_df, config.REPORTS_DIR / "churn_model_comparison.csv", index=False)
    if imp_df is not None:
        save_csv(imp_df, config.REPORTS_DIR / "churn_feature_importance.csv", index=False)

    # Score the full customer base and export churn risk for the dashboard
    X_full = X.copy()
    if best_model_name == "Logistic Regression":
        proba_full = best_model.predict_proba(scaler.transform(X_full))[:, 1]
    else:
        proba_full = best_model.predict_proba(X_full)[:, 1]

    churn_scores = features[["Customer_ID", "Churned"]].copy()
    churn_scores["Churn_Probability"] = proba_full
    churn_scores["Risk_Tier"] = pd.cut(
        churn_scores["Churn_Probability"], bins=[-0.01, 0.33, 0.66, 1.0],
        labels=["Low Risk", "Medium Risk", "High Risk"],
    )
    save_csv(churn_scores, config.CHURN_PRED_FILE, index=False)

    config.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_model, config.MODELS_DIR / "churn_model.pkl")
    joblib.dump(scaler, config.MODELS_DIR / "churn_scaler.pkl")
    joblib.dump(feature_names, config.MODELS_DIR / "churn_feature_names.pkl")

    logger.info("Churn prediction pipeline complete. Risk scores saved to %s", config.CHURN_PRED_FILE)
    return results_df, churn_scores


if __name__ == "__main__":
    run()
