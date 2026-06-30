"""
09_generate_kpi_report.py
----------------------------
Stage 9 of the analytics pipeline: Automated KPI & Executive Summary Report.

Aggregates the outputs of every prior stage (cleaned data, RFM, CLV,
segmentation, cohort retention) into:
    1. reports/kpi_summary.csv      — flat key/value KPI table (dashboard-ready)
    2. reports/executive_summary.txt — formatted, stakeholder-ready report
    3. reports/category_kpis.csv     — revenue/order/customer breakdown by category
    4. reports/regional_kpis.csv     — revenue/order/customer breakdown by region

This is the script a 2nd-year analyst would put on a schedule (cron / Airflow
/ Power Automate) to refresh a "KPI pack" automatically every time new data
lands, instead of manually recalculating numbers in Excel.

Run:
    python -m src.generate_kpi_report
"""

from datetime import datetime

import numpy as np
import pandas as pd

from src import config
from src.utils import fmt_currency, fmt_pct, get_logger, load_csv, save_csv

logger = get_logger(__name__)


def compute_kpis(df: pd.DataFrame, rfm: pd.DataFrame, clv: pd.DataFrame, segments: pd.DataFrame) -> dict:
    kpis = {}

    kpis["Total_Revenue"] = df["Revenue"].sum()
    kpis["Total_Orders"] = df["Order_ID"].nunique()
    kpis["Avg_Order_Value"] = kpis["Total_Revenue"] / kpis["Total_Orders"]
    kpis["Total_Units_Sold"] = df["Quantity"].sum()
    kpis["Total_Profit"] = df["Profit"].sum()
    kpis["Profit_Margin_Pct"] = kpis["Total_Profit"] / kpis["Total_Revenue"] * 100

    kpis["Total_Customers"] = df["Customer_ID"].nunique()
    kpis["Revenue_Per_Customer"] = kpis["Total_Revenue"] / kpis["Total_Customers"]
    kpis["Avg_Orders_Per_Customer"] = kpis["Total_Orders"] / kpis["Total_Customers"]

    repeat_customers = (df.groupby("Customer_ID")["Order_ID"].nunique() > 1).sum()
    kpis["Repeat_Customers"] = int(repeat_customers)
    kpis["Repeat_Customer_Rate"] = repeat_customers / kpis["Total_Customers"] * 100
    kpis["One_Time_Customers"] = kpis["Total_Customers"] - kpis["Repeat_Customers"]

    kpis["Total_SKUs"] = df["Product_ID"].nunique()
    kpis["Avg_Items_Per_Order"] = df["Quantity"].sum() / kpis["Total_Orders"]
    kpis["Total_Categories"] = df["Product_Category"].nunique()

    kpis["Avg_Customer_Lifetime_Value"] = clv["CLV_Simple"].mean()
    kpis["Customer_Acquisition_Cost"] = config.CUSTOMER_ACQUISITION_COST
    kpis["CLV_to_CAC_Ratio"] = kpis["Avg_Customer_Lifetime_Value"] / config.CUSTOMER_ACQUISITION_COST
    kpis["Profit_Per_Customer"] = kpis["Total_Profit"] / kpis["Total_Customers"]
    kpis["CAC_Payback_Months"] = clv["CAC_Payback_Months"].replace(0, np.nan).mean()

    churned = (rfm["Recency"] > config.CHURN_RECENCY_THRESHOLD_DAYS * 2).sum()  # 180-day "hard churn" view
    kpis["Churned_Customers"] = int(churned)
    kpis["Churn_Rate"] = churned / len(rfm) * 100
    kpis["Retention_Rate"] = 100 - kpis["Churn_Rate"]
    kpis["Avg_Days_Since_Purchase"] = rfm["Recency"].mean()

    kpis["Analysis_Start_Date"] = df["Order_Date"].min().date().isoformat()
    kpis["Analysis_End_Date"] = df["Order_Date"].max().date().isoformat()
    period_days = (df["Order_Date"].max() - df["Order_Date"].min()).days
    kpis["Analysis_Period_Days"] = period_days
    kpis["Avg_Daily_Revenue"] = kpis["Total_Revenue"] / period_days
    kpis["Avg_Daily_Orders"] = kpis["Total_Orders"] / period_days

    for cluster_name, grp in segments.groupby("Cluster_Name"):
        kpis[f"{cluster_name}_Count"] = len(grp)
        kpis[f"{cluster_name}_Percentage"] = len(grp) / len(segments) * 100

    return kpis


def category_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    total_revenue = df["Revenue"].sum()
    total_orders = df["Order_ID"].nunique()

    breakdown = df.groupby("Product_Category").agg(
        Total_Revenue=("Revenue", "sum"),
        Avg_Order_Value=("Revenue", "mean"),
        Order_Count=("Order_ID", "nunique"),
        Customer_Count=("Customer_ID", "nunique"),
        Units_Sold=("Quantity", "sum"),
        SKU_Count=("Product_ID", "nunique"),
    ).reset_index()

    breakdown["Revenue_Share"] = (breakdown["Total_Revenue"] / total_revenue * 100).round(2)
    breakdown["Order_Share"] = (breakdown["Order_Count"] / total_orders * 100).round(2)
    return breakdown.sort_values("Total_Revenue", ascending=False)


def regional_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    total_revenue = df["Revenue"].sum()
    total_customers = df["Customer_ID"].nunique()

    breakdown = df.groupby("Region").agg(
        Total_Revenue=("Revenue", "sum"),
        Avg_Order_Value=("Revenue", "mean"),
        Order_Count=("Order_ID", "nunique"),
        Customer_Count=("Customer_ID", "nunique"),
        Units_Sold=("Quantity", "sum"),
    ).reset_index()

    breakdown["Revenue_Share"] = (breakdown["Total_Revenue"] / total_revenue * 100).round(2)
    breakdown["Customer_Penetration"] = (breakdown["Customer_Count"] / total_customers * 100).round(2)
    return breakdown.sort_values("Total_Revenue", ascending=False)


def write_executive_summary(kpis: dict, category_df: pd.DataFrame, segments: pd.DataFrame, out_path):
    top_categories = category_df.head(4)
    seg_summary = segments.groupby("Cluster_Name").agg(
        Size=("Customer_ID", "count"), Revenue=("Monetary", "sum"),
        Avg_Frequency=("Frequency", "mean"), Avg_Recency=("Recency", "mean"),
    ).reset_index().sort_values("Revenue", ascending=False)
    total_seg_revenue = seg_summary["Revenue"].sum()

    lines = [
        "", "=" * 80, "RETAIL & MARKETING ANALYTICS", "EXECUTIVE SUMMARY REPORT", "=" * 80, "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Analysis Period: {kpis['Analysis_Start_Date']} to {kpis['Analysis_End_Date']}", "",
        "=" * 80, "1. KEY BUSINESS METRICS", "=" * 80, "",
        "FINANCIAL PERFORMANCE:",
        f"  - Total Revenue: {fmt_currency(kpis['Total_Revenue'])}",
        f"  - Total Profit: {fmt_currency(kpis['Total_Profit'])}",
        f"  - Profit Margin: {fmt_pct(kpis['Profit_Margin_Pct'])}",
        f"  - Average Order Value: {fmt_currency(kpis['Avg_Order_Value'])}", "",
        "CUSTOMER METRICS:",
        f"  - Total Customers: {kpis['Total_Customers']:,}",
        f"  - Repeat Customer Rate: {fmt_pct(kpis['Repeat_Customer_Rate'])}",
        f"  - Customer Retention Rate: {fmt_pct(kpis['Retention_Rate'])}",
        f"  - Churn Rate: {fmt_pct(kpis['Churn_Rate'])}",
        f"  - Average CLV: {fmt_currency(kpis['Avg_Customer_Lifetime_Value'])}", "",
        "OPERATIONAL METRICS:",
        f"  - Total Orders: {kpis['Total_Orders']:,}",
        f"  - Total Units Sold: {kpis['Total_Units_Sold']:,}",
        f"  - Avg Orders per Customer: {kpis['Avg_Orders_Per_Customer']:.2f}",
        f"  - Avg Items per Order: {kpis['Avg_Items_Per_Order']:.2f}", "",
        "MARKETING EFFICIENCY:",
        f"  - CLV/CAC Ratio: {kpis['CLV_to_CAC_Ratio']:.2f}x",
        f"  - Customer Acquisition Cost: {fmt_currency(kpis['Customer_Acquisition_Cost'])}",
        f"  - Profit per Customer: {fmt_currency(kpis['Profit_Per_Customer'])}",
        f"  - CAC Payback Period: {kpis['CAC_Payback_Months']:.1f} months", "",
        "=" * 80, "2. CUSTOMER SEGMENTATION INSIGHTS", "=" * 80, "",
    ]

    for _, row in seg_summary.iterrows():
        pct_rev = row["Revenue"] / total_seg_revenue * 100
        pct_cust = row["Size"] / seg_summary["Size"].sum() * 100
        lines += [
            f"{row['Cluster_Name']}:",
            f"  - Size: {int(row['Size']):,} customers ({pct_cust:.1f}%)",
            f"  - Revenue Contribution: {fmt_currency(row['Revenue'])} ({pct_rev:.1f}%)",
            f"  - Avg Purchase Frequency: {row['Avg_Frequency']:.2f} orders",
            f"  - Avg Recency: {row['Avg_Recency']:.1f} days", "",
        ]

    lines += ["=" * 80, "3. TOP PERFORMING CATEGORIES", "=" * 80, ""]
    for i, row in top_categories.iterrows():
        lines.append(f"{list(top_categories.index).index(i)+1}. {row['Product_Category']}: "
                      f"{fmt_currency(row['Total_Revenue'])} ({row['Revenue_Share']}%)")

    lines += [
        "", "=" * 80, "4. KEY FINDINGS & INSIGHTS", "=" * 80, "",
        "POSITIVE TRENDS:",
        f"  + CLV is {kpis['CLV_to_CAC_Ratio']:.1f}x the acquisition cost (Healthy benchmark: >3.0x)",
        f"  + {fmt_pct(kpis['Repeat_Customer_Rate'])} of customers make repeat purchases",
        f"  + Average order value is {fmt_currency(kpis['Avg_Order_Value'])}", "",
        "AREAS FOR IMPROVEMENT:",
        f"  ! Churn rate of {fmt_pct(kpis['Churn_Rate'])} requires proactive retention work",
        f"  ! {kpis['One_Time_Customers']:,} customers have made only one purchase to date", "",
        "OPPORTUNITIES:",
        "  - Prioritize win-back campaigns for the At-Risk / Lost segments",
        "  - Double down on the top-2 revenue categories while testing growth in laggards",
        "  - Personalize marketing cadence and offers by behavioral segment", "",
        "=" * 80, "5. STRATEGIC RECOMMENDATIONS", "=" * 80, "",
        "IMMEDIATE (0-30 Days): loyalty program for VIPs, win-back campaign for at-risk customers,",
        "  automated churn-risk alerts to the retention team.",
        "SHORT-TERM (2-3 Months): personalized email journeys by segment, discount-sensitivity",
        "  testing, referral program pilot.",
        "LONG-TERM (6-12 Months): productionize the churn model, build a recommendation engine,",
        "  formal customer-success motion for high-CLV accounts.", "",
        "=" * 80, "END OF EXECUTIVE SUMMARY", "=" * 80, "",
    ]

    out_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Executive summary written to %s", out_path)


def run():
    df = load_csv(config.FEATURED_SALES_FILE, parse_dates=["Order_Date", "Ship_Date"])
    rfm = load_csv(config.RFM_FILE)
    clv = load_csv(config.CLV_FILE)
    segments = load_csv(config.SEGMENTS_FILE)

    kpis = compute_kpis(df, rfm, clv, segments)
    category_df = category_breakdown(df)
    regional_df = regional_breakdown(df)

    kpi_df = pd.DataFrame(list(kpis.items()), columns=["KPI", "Value"])
    save_csv(kpi_df, config.REPORTS_DIR / "kpi_summary.csv", index=False)
    save_csv(category_df, config.REPORTS_DIR / "category_kpis.csv", index=False)
    save_csv(regional_df, config.REPORTS_DIR / "regional_kpis.csv", index=False)

    write_executive_summary(kpis, category_df, segments, config.REPORTS_DIR / "executive_summary.txt")

    logger.info("KPI report generation complete. See reports/ for all output files.")
    return kpis


if __name__ == "__main__":
    run()
