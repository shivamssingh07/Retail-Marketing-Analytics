"""
src/ml/sales_prediction.py
-----------------------------
Machine Learning Module 2: Order-Level Sales (Revenue) Prediction.

Predicts the Sales value of an individual order line from attributes known
at order time -- Quantity, Unit_Price, Discount, Product_Category, Region,
Segment, Order_Priority, and calendar features. Unit_Price and Quantity are
known the moment an order is placed (they are not future/leaked
information), so they are legitimate model inputs; the resulting feature
importances are themselves a useful business finding -- e.g. confirming
that price and volume are the dominant drivers of order value while
discounting and region contribute comparatively little, which is exactly
the kind of "what actually drives revenue" question a stakeholder asks.

Use cases:
    - Estimating expected order value at checkout/quoting time
    - Flagging orders whose actual sales deviate strongly from expectation
      (potential data-entry errors or pricing anomalies)
    - A clean, classic tabular regression problem for the portfolio (as
      distinct from the monthly time-series forecast in sales_forecasting.py)

Models compared:
    - Linear Regression (baseline)
    - Random Forest Regressor
    - XGBoost Regressor (final/production model)

Evaluation: R², MAE, RMSE + feature importance plot.

Run:
    python -m src.ml.sales_prediction
"""

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from src import config
from src.utils import get_logger, load_csv, save_csv, save_fig, setup_plot_style

logger = get_logger(__name__)

try:
    from xgboost import XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

TARGET = "Sales"
CATEGORICAL_FEATURES = ["Segment", "Region", "Product_Category", "Product_Sub_Category", "Order_Priority"]
NUMERIC_FEATURES = ["Quantity", "Unit_Price", "Discount", "Shipping_Cost", "Month", "Quarter", "Is_Weekend"]


def prepare_xy(df: pd.DataFrame):
    data = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES + [TARGET]].dropna()
    X = pd.get_dummies(data[NUMERIC_FEATURES + CATEGORICAL_FEATURES], columns=CATEGORICAL_FEATURES, drop_first=True)
    y = data[TARGET]
    return X, y


def train_models(X_train, X_test, y_train, y_test):
    models = {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(
            n_estimators=200, max_depth=10, random_state=config.RANDOM_STATE, n_jobs=-1
        ),
    }
    if XGBOOST_AVAILABLE:
        models["XGBoost"] = XGBRegressor(
            n_estimators=300, max_depth=5, learning_rate=0.05,
            subsample=0.9, colsample_bytree=0.9, random_state=config.RANDOM_STATE,
        )

    results = []
    fitted = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        results.append({
            "Model": name,
            "R2_Score": r2_score(y_test, preds),
            "MAE": mean_absolute_error(y_test, preds),
            "RMSE": np.sqrt(mean_squared_error(y_test, preds)),
        })
        fitted[name] = {"model": model, "preds": preds}

    results_df = pd.DataFrame(results).sort_values("R2_Score", ascending=False)
    return results_df, fitted


def plot_actual_vs_predicted(y_test, preds, model_name: str):
    setup_plot_style()
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.scatter(y_test, preds, alpha=0.4, s=18, color="#2563eb")
    lims = [0, max(y_test.max(), preds.max())]
    ax.plot(lims, lims, "--", color="red", label="Perfect Prediction")
    ax.set_xlabel("Actual Sales ($)")
    ax.set_ylabel("Predicted Sales ($)")
    ax.set_title(f"Actual vs Predicted Sales — {model_name}", fontweight="bold")
    ax.legend()
    fig.tight_layout()
    save_fig(fig, "31_sales_prediction_actual_vs_predicted.png")


def plot_feature_importance(model, feature_names, model_name: str):
    setup_plot_style()
    if not hasattr(model, "feature_importances_"):
        return None
    imp_df = pd.DataFrame({
        "Feature": feature_names, "Importance": model.feature_importances_
    }).sort_values("Importance", ascending=False).head(12)

    fig, ax = plt.subplots(figsize=(9, 7))
    sns.barplot(data=imp_df, x="Importance", y="Feature", hue="Feature", legend=False,
                palette="mako", ax=ax)
    ax.set_title(f"Top Feature Importances — {model_name} (Sales Prediction)", fontweight="bold")
    fig.tight_layout()
    save_fig(fig, "32_sales_prediction_feature_importance.png")
    return imp_df


def run():
    df = load_csv(config.FEATURED_SALES_FILE, parse_dates=["Order_Date", "Ship_Date"])
    X, y = prepare_xy(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=config.RANDOM_STATE
    )

    results_df, fitted = train_models(X_train, X_test, y_train, y_test)
    logger.info("Sales prediction model comparison:\n%s", results_df.to_string(index=False))

    best_model_name = results_df.iloc[0]["Model"]
    best_model = fitted[best_model_name]["model"]
    best_preds = fitted[best_model_name]["preds"]
    logger.info("Best model by R^2: %s (R2=%.3f)", best_model_name, results_df.iloc[0]["R2_Score"])

    plot_actual_vs_predicted(y_test, best_preds, best_model_name)
    imp_df = plot_feature_importance(best_model, X.columns.tolist(), best_model_name)

    save_csv(results_df, config.REPORTS_DIR / "sales_prediction_model_comparison.csv", index=False)
    if imp_df is not None:
        save_csv(imp_df, config.REPORTS_DIR / "sales_prediction_feature_importance.csv", index=False)

    config.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_model, config.MODELS_DIR / "sales_prediction_model.pkl")
    joblib.dump(X.columns.tolist(), config.MODELS_DIR / "sales_prediction_feature_names.pkl")

    logger.info("Sales prediction pipeline complete.")
    return results_df


if __name__ == "__main__":
    run()
