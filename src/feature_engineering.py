"""
02_feature_engineering.py
--------------------------
Stage 2 of the analytics pipeline: Feature Engineering.

Takes the cleaned transactional dataset and enriches it with:
    - Calendar features (year, month, quarter, day, week, weekday name, season)
    - Weekend / month-start / month-end flags
    - Financial features (discount amount, net revenue, profit margin/ratio)
    - Delivery features (delivery days, delivery speed category)
    - Customer-level aggregates (order count, repeat-customer flag)
    - Product-level aggregates (total/avg sales, order count)
    - A categorical Sales_Category bucket (Low/Medium/High/Very High)

Output is the single "analytics-ready" fact table used by every downstream
script (EDA, RFM, CLV, segmentation, forecasting, ML, SQL load, Power BI,
and the Streamlit dashboard).

Run:
    python -m src.feature_engineering
"""

import numpy as np
import pandas as pd

from src import config
from src.utils import get_logger, load_csv, save_csv

logger = get_logger(__name__)

SEASON_MAP = {
    12: "Winter", 1: "Winter", 2: "Winter",
    3: "Spring", 4: "Spring", 5: "Spring",
    6: "Summer", 7: "Summer", 8: "Summer",
    9: "Fall", 10: "Fall", 11: "Fall",
}


def add_date_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Order_Date"] = pd.to_datetime(df["Order_Date"])
    df["Ship_Date"] = pd.to_datetime(df["Ship_Date"])

    df["Year"] = df["Order_Date"].dt.year
    df["Month"] = df["Order_Date"].dt.month
    df["Month_Name"] = df["Order_Date"].dt.month_name()
    df["Quarter"] = df["Order_Date"].dt.quarter
    df["Day"] = df["Order_Date"].dt.day
    df["Day_of_Week"] = df["Order_Date"].dt.dayofweek  # Monday=0
    df["Day_Name"] = df["Order_Date"].dt.day_name()
    df["Week_of_Year"] = df["Order_Date"].dt.isocalendar().week.astype(int)

    df["Is_Weekend"] = df["Day_of_Week"].isin([5, 6]).astype(int)
    df["Is_Month_Start"] = df["Order_Date"].dt.is_month_start.astype(int)
    df["Is_Month_End"] = df["Order_Date"].dt.is_month_end.astype(int)

    df["Season"] = df["Month"].map(SEASON_MAP)
    return df


def add_financial_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Discount_Amount"] = df["Sales"] * df["Discount"]
    df["Net_Revenue"] = df["Sales"] - df["Discount_Amount"]

    # Avoid division by zero
    safe_sales = df["Sales"].replace(0, np.nan)
    df["Profit_Margin"] = (df["Profit"] / safe_sales * 100).fillna(0)
    df["Profit_Ratio"] = (df["Profit"] / safe_sales).fillna(0)
    return df


def add_delivery_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Delivery_Days"] = (df["Ship_Date"] - df["Order_Date"]).dt.days.clip(lower=0)

    bins = [-1, 1, 3, 7, np.inf]
    labels = ["Same/Next Day", "2-3 Days", "4-7 Days", "7+ Days"]
    df["Delivery_Category"] = pd.cut(df["Delivery_Days"], bins=bins, labels=labels)
    return df


def add_customer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    order_counts = df.groupby("Customer_ID")["Order_ID"].transform("nunique")
    df["Customer_Order_Count"] = order_counts
    df["Is_Repeat_Customer"] = (df["Customer_Order_Count"] > 1).astype(int)
    return df


def add_product_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    grp = df.groupby("Product_ID")["Sales"]
    df["Product_Total_Sales"] = grp.transform("sum")
    df["Product_Avg_Sales"] = grp.transform("mean")
    df["Product_Order_Count"] = df.groupby("Product_ID")["Order_ID"].transform("nunique")
    return df


def add_sales_category(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    quartiles = df["Sales"].quantile([0.25, 0.5, 0.75]).values
    bins = [-np.inf, quartiles[0], quartiles[1], quartiles[2], np.inf]
    labels = ["Low", "Medium", "High", "Very High"]
    df["Sales_Category"] = pd.cut(df["Sales"], bins=bins, labels=labels)
    return df


def run():
    logger.info("Loading cleaned dataset from %s", config.CLEAN_SALES_FILE)
    df = load_csv(config.CLEAN_SALES_FILE, parse_dates=["Order_Date", "Ship_Date"])

    df = add_date_features(df)
    df = add_financial_features(df)
    df = add_delivery_features(df)
    df = add_customer_features(df)
    df = add_product_features(df)
    df = add_sales_category(df)

    logger.info("Feature-engineered dataset shape: %s, columns: %d", df.shape, df.shape[1])
    save_csv(df, config.FEATURED_SALES_FILE)
    logger.info("Saved to %s", config.FEATURED_SALES_FILE)
    return df


if __name__ == "__main__":
    run()
