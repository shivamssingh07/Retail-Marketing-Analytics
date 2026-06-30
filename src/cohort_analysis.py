"""
07_cohort_analysis.py
-----------------------
Stage 7 of the analytics pipeline: Cohort Retention Analysis.

Groups customers into monthly acquisition cohorts (based on the month of
their first purchase) and tracks what % of each cohort is still active in
each subsequent "cohort month" (0 = acquisition month, 1 = next month, ...).

This produces the classic cohort retention heatmap/table used in almost
every SaaS / retail / marketing analytics interview and dashboard.

Run:
    python -m src.cohort_analysis
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src import config
from src.utils import get_logger, load_csv, save_csv, save_fig, setup_plot_style

logger = get_logger(__name__)


def build_cohorts(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Order_Month"] = df["Order_Date"].dt.to_period("M")

    first_purchase = df.groupby("Customer_ID")["Order_Month"].min().rename("Cohort_Month")
    df = df.merge(first_purchase, on="Customer_ID", how="left")

    df["Cohort_Index"] = (
        (df["Order_Month"].dt.year - df["Cohort_Month"].dt.year) * 12
        + (df["Order_Month"].dt.month - df["Cohort_Month"].dt.month)
    )
    return df


def retention_table(df: pd.DataFrame) -> pd.DataFrame:
    cohort_data = (
        df.groupby(["Cohort_Month", "Cohort_Index"])["Customer_ID"]
        .nunique()
        .reset_index()
    )
    cohort_pivot = cohort_data.pivot(
        index="Cohort_Month", columns="Cohort_Index", values="Customer_ID"
    )

    cohort_sizes = cohort_pivot.iloc[:, 0]
    retention = cohort_pivot.divide(cohort_sizes, axis=0) * 100
    retention.index = retention.index.astype(str)
    retention.index.name = "Cohort"
    return retention.round(2)


def plot_retention_heatmap(retention: pd.DataFrame):
    setup_plot_style()
    fig, ax = plt.subplots(figsize=(14, 9))
    sns.heatmap(
        retention,
        annot=True,
        fmt=".0f",
        cmap="YlGnBu",
        cbar_kws={"label": "Retention %"},
        ax=ax,
        linewidths=0.5,
    )
    ax.set_title("Monthly Cohort Retention Analysis (%)", fontsize=15, fontweight="bold")
    ax.set_xlabel("Months Since First Purchase")
    ax.set_ylabel("Acquisition Cohort")
    fig.tight_layout()
    save_fig(fig, "23_cohort_retention.png")


def average_retention_curve(retention: pd.DataFrame) -> pd.Series:
    return retention.mean(axis=0).round(2)


def run():
    df = load_csv(config.FEATURED_SALES_FILE, parse_dates=["Order_Date", "Ship_Date"])
    df = build_cohorts(df)

    retention = retention_table(df)
    plot_retention_heatmap(retention)

    avg_curve = average_retention_curve(retention)
    logger.info("Average retention curve (month 0-N):\n%s", avg_curve)

    month1_retention = avg_curve.get(1, np.nan)
    logger.info("Average Month-1 retention across all cohorts: %.2f%%", month1_retention)

    save_csv(retention.reset_index(), config.REPORTS_DIR / "cohort_retention.csv", index=False)
    save_csv(
        avg_curve.reset_index().rename(columns={"index": "Cohort_Index", 0: "Avg_Retention_Pct"}),
        config.REPORTS_DIR / "cohort_retention_avg_curve.csv",
        index=False,
    )

    logger.info("Cohort analysis complete. Output saved to reports/cohort_retention.csv")
    return retention


if __name__ == "__main__":
    run()
