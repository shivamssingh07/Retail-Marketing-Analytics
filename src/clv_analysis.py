"""
05_clv_analysis.py
--------------------
Stage 5 of the analytics pipeline: Customer Lifetime Value (CLV) Analysis.

Computes two complementary CLV views:

1. CLV_Historical: actual total revenue generated to date (ground truth).
2. CLV_Predictive: a forward-looking estimate using the standard formula

       CLV = Avg Order Value x Purchase Frequency x Avg Customer Lifespan (years)
                                                   x Gross Margin %

   where:
       - Avg Order Value      = Total Revenue / Order Count
       - Purchase Frequency   = Order Count / Customer Lifespan (years)
       - Avg Customer Lifespan = (Last Purchase - First Purchase), with a
         floor applied for single-purchase customers so CLV is not zero.
       - Gross Margin %       = Profit / Revenue, computed per customer.

Also derives CLV:CAC ratio and CAC payback period using the CAC assumption
in config.py, both standard marketing-efficiency metrics recruiters look for.

Run:
    python -m src.clv_analysis
"""

import numpy as np
import pandas as pd

from src import config
from src.utils import get_logger, load_csv, save_csv

logger = get_logger(__name__)

MIN_LIFESPAN_DAYS = 30  # floor for single/near-single purchase customers


def compute_clv(df: pd.DataFrame) -> pd.DataFrame:
    customer = df.groupby("Customer_ID").agg(
        Total_Revenue=("Revenue", "sum"),
        Total_Profit=("Profit", "sum"),
        Order_Count=("Order_ID", "nunique"),
        First_Purchase=("Order_Date", "min"),
        Last_Purchase=("Order_Date", "max"),
    ).reset_index()

    customer["Lifespan_Days"] = (
        customer["Last_Purchase"] - customer["First_Purchase"]
    ).dt.days.clip(lower=MIN_LIFESPAN_DAYS)

    customer["Avg_Order_Value"] = customer["Total_Revenue"] / customer["Order_Count"]
    customer["Purchase_Frequency"] = customer["Order_Count"] / (customer["Lifespan_Days"] / 365.25)
    customer["Gross_Margin_Pct"] = (
        customer["Total_Profit"] / customer["Total_Revenue"].replace(0, np.nan)
    ).fillna(0)

    # --- Historical (actual to-date) CLV ---
    customer["CLV_Historical"] = customer["Total_Revenue"]

    # --- Predictive (forward-looking) CLV ---
    # Project each customer's OBSERVED purchase frequency forward across a
    # FIXED horizon (config.CLV_PROJECTION_YEARS), not their own observed
    # lifespan - using the same lifespan on both sides of the equation
    # would cancel out and silently collapse CLV back to historical revenue.
    customer["CLV_Simple"] = (
        customer["Avg_Order_Value"]
        * customer["Purchase_Frequency"]
        * config.CLV_PROJECTION_YEARS
    )
    # Margin-adjusted predictive CLV: same projection, weighted by each
    # customer's own gross margin so two customers with identical revenue
    # but different profitability aren't valued the same.
    customer["CLV_Predictive"] = customer["CLV_Simple"] * customer["Gross_Margin_Pct"].clip(lower=0.05)

    # --- Marketing efficiency metrics ---
    customer["CAC"] = config.CUSTOMER_ACQUISITION_COST
    customer["CLV_to_CAC_Ratio"] = customer["CLV_Simple"] / customer["CAC"]
    customer["CAC_Payback_Months"] = (
        customer["CAC"] / (customer["Total_Profit"] / customer["Order_Count"]).replace(0, np.nan)
    ).fillna(0).clip(lower=0)

    return customer


def bucket_clv(customer: pd.DataFrame) -> pd.DataFrame:
    customer = customer.copy()
    q25, q75 = customer["CLV_Simple"].quantile([0.25, 0.75])
    customer["CLV_Category"] = pd.cut(
        customer["CLV_Simple"],
        bins=[-np.inf, q25, q75, np.inf],
        labels=["Low", "Medium", "High"],
    )
    return customer


def run() -> pd.DataFrame:
    df = load_csv(config.FEATURED_SALES_FILE, parse_dates=["Order_Date", "Ship_Date"])

    clv = compute_clv(df)
    clv = bucket_clv(clv)

    logger.info("Average CLV (simple): $%.2f", clv["CLV_Simple"].mean())
    logger.info("Average CLV:CAC ratio: %.2fx", clv["CLV_to_CAC_Ratio"].mean())
    logger.info("CLV category distribution:\n%s", clv["CLV_Category"].value_counts())

    save_csv(clv, config.CLV_FILE)
    logger.info("CLV analysis saved to %s (n=%d customers)", config.CLV_FILE, len(clv))
    return clv


if __name__ == "__main__":
    run()
