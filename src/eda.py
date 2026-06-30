"""
03_eda.py
---------
Stage 3 of the analytics pipeline: Exploratory Data Analysis.

Generates a suite of static (matplotlib/seaborn) and interactive (plotly)
charts into images/eda/, plus a plain-text key-findings report into
reports/. This script is intentionally chart-heavy: in a real analytics
job, EDA artifacts are what go into the deck before any modeling starts.

Run:
    python -m src.eda
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src import config
from src.utils import get_logger, load_csv, save_fig, setup_plot_style

logger = get_logger(__name__)

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logger.warning("plotly not installed - interactive HTML charts will be skipped. "
                    "Install with: pip install plotly")


def load_data() -> pd.DataFrame:
    df = load_csv(config.FEATURED_SALES_FILE, parse_dates=["Order_Date", "Ship_Date"])
    logger.info("Loaded feature-engineered dataset: %s", df.shape)
    return df


# ---------------------------------------------------------------------------
# Static (matplotlib / seaborn) charts
# ---------------------------------------------------------------------------
def plot_numerical_distributions(df: pd.DataFrame):
    cols = ["Sales", "Profit", "Discount", "Quantity", "Profit_Margin", "Shipping_Cost"]
    fig, axes = plt.subplots(2, 3, figsize=(16, 9))
    for ax, col in zip(axes.flat, cols):
        sns.histplot(df[col], kde=True, ax=ax, color="#2563eb")
        ax.set_title(col.replace("_", " "))
    fig.suptitle("Numerical Feature Distributions", fontsize=16, fontweight="bold")
    fig.tight_layout()
    save_fig(fig, "05_numerical_distributions.png")


def plot_categorical_distributions(df: pd.DataFrame):
    cols = ["Segment", "Region", "Product_Category", "Order_Priority"]
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    for ax, col in zip(axes.flat, cols):
        order = df[col].value_counts().index
        sns.countplot(data=df, x=col, order=order, ax=ax, palette="viridis", hue=col, legend=False)
        ax.set_title(f"Order Count by {col.replace('_', ' ')}")
        ax.tick_params(axis="x", rotation=30)
    fig.suptitle("Categorical Feature Distributions", fontsize=16, fontweight="bold")
    fig.tight_layout()
    save_fig(fig, "06_categorical_distributions.png")


def plot_correlation_matrix(df: pd.DataFrame):
    numeric_cols = ["Sales", "Profit", "Quantity", "Discount", "Shipping_Cost",
                     "Unit_Price", "Profit_Margin", "Net_Revenue", "Delivery_Days"]
    corr = df[numeric_cols].corr()
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax,
                linewidths=0.5)
    ax.set_title("Correlation Matrix - Numeric Features")
    fig.tight_layout()
    save_fig(fig, "09_correlation_matrix.png")


def plot_monthly_trend_static(df: pd.DataFrame):
    monthly = df.groupby(df["Order_Date"].dt.to_period("M"))["Revenue"].sum()
    fig, ax = plt.subplots(figsize=(12, 5))
    monthly.plot(ax=ax, marker="o", color="#0f766e")
    ax.set_title("Monthly Revenue Trend")
    ax.set_ylabel("Revenue ($)")
    ax.set_xlabel("Month")
    fig.tight_layout()
    save_fig(fig, "10_monthly_revenue_trend.png")


def plot_top_products(df: pd.DataFrame, n: int = 10):
    top = df.groupby("Product_Name")["Sales"].sum().sort_values(ascending=False).head(n)
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x=top.values, y=top.index, ax=ax, palette="mako", hue=top.index, legend=False)
    ax.set_title(f"Top {n} Products by Revenue")
    ax.set_xlabel("Revenue ($)")
    fig.tight_layout()
    save_fig(fig, "15_top_products.png")


def plot_box_outliers(df: pd.DataFrame):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    sns.boxplot(y=df["Sales_Original"], ax=axes[0], color="#f87171")
    axes[0].set_title("Sales - Before Outlier Treatment")
    sns.boxplot(y=df["Sales"], ax=axes[1], color="#34d399")
    axes[1].set_title("Sales - After IQR Capping")
    fig.tight_layout()
    save_fig(fig, "04_outliers_before_after.png")


# ---------------------------------------------------------------------------
# Interactive (plotly) charts -> saved as standalone HTML for the README /
# dashboard storytelling. These are optional and degrade gracefully.
# ---------------------------------------------------------------------------
def plot_interactive_charts(df: pd.DataFrame):
    if not PLOTLY_AVAILABLE:
        return

    out_dir = config.EDA_IMAGES_DIR

    # Revenue by category - interactive bar
    cat_rev = df.groupby("Product_Category", as_index=False)["Revenue"].sum() \
        .sort_values("Revenue", ascending=False)
    fig = px.bar(cat_rev, x="Product_Category", y="Revenue", color="Product_Category",
                 title="Revenue by Product Category", text_auto=".2s")
    fig.write_html(out_dir / "07_sales_by_category.html")

    # Monthly trend - interactive line
    monthly = df.groupby(df["Order_Date"].dt.to_period("M").astype(str), as_index=False)["Revenue"].sum()
    monthly.columns = ["Month", "Revenue"]
    fig = px.line(monthly, x="Month", y="Revenue", markers=True,
                  title="Monthly Revenue Trend (Interactive)")
    fig.write_html(out_dir / "10_monthly_sales_trend.html")

    # Region treemap
    region_rev = df.groupby(["Region", "Product_Category"], as_index=False)["Revenue"].sum()
    fig = px.treemap(region_rev, path=["Region", "Product_Category"], values="Revenue",
                      title="Revenue Breakdown: Region -> Category")
    fig.write_html(out_dir / "08_region_category_treemap.html")

    logger.info("Interactive plotly charts saved to %s", out_dir)


# ---------------------------------------------------------------------------
# Key findings text report
# ---------------------------------------------------------------------------
def write_key_findings(df: pd.DataFrame):
    total_revenue = df["Revenue"].sum()
    total_orders = df["Order_ID"].nunique()
    total_customers = df["Customer_ID"].nunique()
    avg_order_value = total_revenue / total_orders
    top_category = df.groupby("Product_Category")["Revenue"].sum().idxmax()
    top_region = df.groupby("Region")["Revenue"].sum().idxmax()
    weekend_share = df[df["Is_Weekend"] == 1]["Revenue"].sum() / total_revenue * 100
    corr_disc_profit = df["Discount"].corr(df["Profit_Margin"])

    lines = [
        "=" * 80,
        "EXPLORATORY DATA ANALYSIS - KEY FINDINGS",
        "=" * 80,
        "",
        f"Dataset: {len(df):,} order lines | {total_orders:,} orders | "
        f"{total_customers:,} customers",
        f"Date range: {df['Order_Date'].min().date()} to {df['Order_Date'].max().date()}",
        "",
        "REVENUE & SALES",
        f"  - Total Revenue: ${total_revenue:,.2f}",
        f"  - Average Order Value: ${avg_order_value:,.2f}",
        f"  - Top Performing Category: {top_category}",
        f"  - Top Performing Region: {top_region}",
        f"  - Weekend orders contribute {weekend_share:.1f}% of total revenue",
        "",
        "RELATIONSHIPS",
        f"  - Correlation between Discount and Profit Margin: {corr_disc_profit:.3f} "
        f"({'inverse - higher discounts erode margin' if corr_disc_profit < 0 else 'positive'})",
        "",
        "DATA QUALITY",
        f"  - {(df['Sales'] != df['Sales_Original']).sum()} Sales values were capped as outliers (IQR method)",
        f"  - {(df['Profit'] != df['Profit_Original']).sum()} Profit values were capped as outliers (IQR method)",
        "",
        "=" * 80,
    ]
    out_path = config.REPORTS_DIR / "03_eda_key_findings.txt"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Key findings report written to %s", out_path)


def run():
    setup_plot_style()
    df = load_data()

    plot_numerical_distributions(df)
    plot_categorical_distributions(df)
    plot_correlation_matrix(df)
    plot_monthly_trend_static(df)
    plot_top_products(df)
    plot_box_outliers(df)
    plot_interactive_charts(df)
    write_key_findings(df)

    logger.info("EDA complete. Charts saved to %s", config.EDA_IMAGES_DIR)


if __name__ == "__main__":
    run()
