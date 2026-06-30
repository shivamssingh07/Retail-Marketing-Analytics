"""
08_sales_forecasting.py
--------------------------
Stage 8 of the analytics pipeline: Sales Forecasting.

Builds a monthly revenue forecast using two complementary approaches so the
project demonstrates both classical statistical forecasting and ML-based
forecasting (a common interview talking point: "compare a baseline
statistical model against a gradient-boosted model"):

    1. Holt-Winters Exponential Smoothing (statsmodels) — captures trend
       and seasonality with minimal feature engineering. Used as the
       interpretable baseline.
    2. XGBoost Regressor on engineered time-series features (lag values,
       rolling means, calendar features) — typically the stronger model,
       and the one exposed in the Streamlit app.

Both models are evaluated on a held-out test window (the most recent N
months) using MAE, RMSE, and MAPE, and a comparison chart is saved.

Run:
    python -m src.sales_forecasting
"""

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error

from src import config
from src.utils import get_logger, load_csv, save_csv, save_fig, setup_plot_style

logger = get_logger(__name__)

try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    logger.warning("statsmodels not installed - Holt-Winters baseline will be skipped.")

try:
    from xgboost import XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning("xgboost not installed - ML forecast will be skipped.")


def build_monthly_series(df: pd.DataFrame) -> pd.Series:
    monthly = df.groupby(df["Order_Date"].dt.to_period("M"))["Revenue"].sum()
    monthly.index = monthly.index.to_timestamp()
    monthly = monthly.asfreq("MS")
    return monthly


def train_test_split_series(series: pd.Series, holdout_months: int):
    train = series.iloc[:-holdout_months]
    test = series.iloc[-holdout_months:]
    return train, test


def evaluate(actual: pd.Series, predicted: np.ndarray) -> dict:
    return {
        "MAE": mean_absolute_error(actual, predicted),
        "RMSE": np.sqrt(mean_squared_error(actual, predicted)),
        "MAPE": mean_absolute_percentage_error(actual, predicted) * 100,
    }


def forecast_holt_winters(train: pd.Series, horizon: int):
    """
    Robust Holt-Winters forecasting.

    Automatically switches to a non-seasonal Holt model when there isn't
    enough historical data for seasonal forecasting.
    """

    if not STATSMODELS_AVAILABLE:
        logger.warning("statsmodels not installed.")
        return None, None

    try:

        # Need at least 24 months for seasonal model
        if len(train) >= 24:

            logger.info(
                "Using Seasonal Holt-Winters (%d months).",
                len(train)
            )

            model = ExponentialSmoothing(
                train,
                trend="add",
                seasonal="add",
                seasonal_periods=12,
                initialization_method="estimated"
            ).fit()

        else:

            logger.warning(
                "Only %d months available. Using Holt model without seasonality.",
                len(train)
            )

            model = ExponentialSmoothing(
                train,
                trend="add",
                seasonal=None,
                initialization_method="estimated"
            ).fit()

        forecast = model.forecast(horizon)

        return model, forecast

    except Exception as e:

        logger.exception(
            "Holt-Winters Forecast Failed: %s",
            e
        )

        return None, None


def build_ml_features(series: pd.Series) -> pd.DataFrame:
    """Build lag / rolling / calendar features for a supervised-learning forecast."""
    feat = pd.DataFrame({"Revenue": series})
    for lag in [1, 2, 3, 6, 12]:
        feat[f"lag_{lag}"] = feat["Revenue"].shift(lag)
    feat["rolling_mean_3"] = feat["Revenue"].shift(1).rolling(3).mean()
    feat["rolling_mean_6"] = feat["Revenue"].shift(1).rolling(6).mean()
    feat["month"] = feat.index.month
    feat["quarter"] = feat.index.quarter
    feat["month_sin"] = np.sin(2 * np.pi * feat["month"] / 12)
    feat["month_cos"] = np.cos(2 * np.pi * feat["month"] / 12)
    feat["time_index"] = np.arange(len(feat))
    return feat


def forecast_xgboost(series: pd.Series, holdout_months: int):
    if not XGBOOST_AVAILABLE:
        return None, None, None

    feat = build_ml_features(series).dropna()

    if len(feat) <= holdout_months:
        logger.warning("Not enough rows for XGBoost forecasting.")
        return None, None, None

    feature_cols = [c for c in feat.columns if c != "Revenue"]

    train_feat = feat.iloc[:-holdout_months]
    test_feat = feat.iloc[-holdout_months:]

    model = XGBRegressor(
        n_estimators=200,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=config.RANDOM_STATE,
    )

    model.fit(train_feat[feature_cols], train_feat["Revenue"])

    preds = model.predict(test_feat[feature_cols])

    return model, pd.Series(preds, index=test_feat.index), feature_cols

def forecast_future_xgboost(model, series: pd.Series, feature_cols, horizon: int) -> pd.Series:
    """Iteratively forecast `horizon` months beyond the end of `series`."""
    history = series.copy()
    future_index = pd.date_range(
        history.index.max() + pd.DateOffset(months=1), periods=horizon, freq="MS"
    )
    preds = []
    for date in future_index:
        history.loc[date] = np.nan  # placeholder so feature builder sees the date
        feat_row = build_ml_features(history).loc[[date], feature_cols]
        pred = model.predict(feat_row)[0]
        history.loc[date] = pred
        preds.append(pred)
    return pd.Series(preds, index=future_index)


def plot_forecast_comparison(train, test, hw_forecast, xgb_forecast, future_xgb):
    setup_plot_style()
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(train.index, train.values, label="Historical (Train)", color="#1f2937")
    ax.plot(test.index, test.values, label="Actual (Test)", color="#16a34a", marker="o")

    if hw_forecast is not None:
        ax.plot(test.index, hw_forecast.values, "--", label="Holt-Winters Forecast", color="#f59e0b")
    if xgb_forecast is not None:
        ax.plot(test.index, xgb_forecast.values, "--", label="XGBoost Forecast (Test)", color="#2563eb")
    if future_xgb is not None:
        ax.plot(future_xgb.index, future_xgb.values, ":", label="XGBoost Forecast (Future)",
                 color="#dc2626", marker="x")

    ax.set_title("Monthly Revenue Forecast: Holt-Winters vs XGBoost", fontsize=15, fontweight="bold")
    ax.set_ylabel("Revenue ($)")
    ax.legend()
    fig.tight_layout()
    save_fig(fig, "28_sales_forecast_comparison.png")


def run():
    df = load_csv(config.FEATURED_SALES_FILE, parse_dates=["Order_Date", "Ship_Date"])
    monthly = build_monthly_series(df)
    logger.info("Monthly revenue series: %d months (%s to %s)",
                len(monthly), monthly.index.min().date(), monthly.index.max().date())

    holdout = config.TRAIN_TEST_SPLIT_DATE_HOLDOUT_MONTHS
       # Prevent invalid holdout size
    if holdout >= len(monthly):
        holdout = max(1, len(monthly) // 4)

        logger.warning(
            "Holdout adjusted to %d months because dataset contains only %d months.",
            holdout,
            len(monthly),
        )

    # Ensure training set has enough observations
    if len(monthly) - holdout < 3:
        holdout = max(1, len(monthly) - 3)

        logger.warning(
            "Holdout reduced to %d months to keep enough training data.",
            holdout,
        )
    train, test = train_test_split_series(monthly, holdout)

    results = {}

    hw_model, hw_forecast = forecast_holt_winters(train, holdout)
    if hw_forecast is not None:
        results["Holt-Winters"] = evaluate(test.values, hw_forecast.values)

    xgb_model, xgb_test_forecast, feature_cols = forecast_xgboost(monthly, holdout)
    if xgb_test_forecast is not None:
        results["XGBoost"] = evaluate(test.values, xgb_test_forecast.values)
        future_forecast = forecast_future_xgboost(
            xgb_model, monthly, feature_cols, config.FORECAST_HORIZON_MONTHS
        )
    else:
        future_forecast = None

    results_df = pd.DataFrame(results).T
    logger.info("Forecast model comparison:\n%s", results_df.to_string())

    plot_forecast_comparison(train, test, hw_forecast, xgb_test_forecast, future_forecast)

    if future_forecast is not None:
        forecast_out = future_forecast.reset_index()
        forecast_out.columns = ["Month", "Forecasted_Revenue"]
        save_csv(forecast_out, config.FORECAST_FILE, index=False)
        logger.info("Future forecast saved to %s:\n%s", config.FORECAST_FILE, forecast_out)

    save_csv(results_df.reset_index().rename(columns={"index": "Model"}),
              config.REPORTS_DIR / "forecast_model_comparison.csv", index=False)

    return results_df, future_forecast


if __name__ == "__main__":
    run()
