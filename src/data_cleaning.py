"""
01_data_cleaning.py
--------------------
Stage 1 of the analytics pipeline: Data Cleaning.

Responsibilities:
    1. Load the raw transactional retail dataset.
    2. Validate schema (expected columns / dtypes).
    3. Handle missing values.
    4. Remove exact duplicate transactions.
    5. Fix data types (dates, categoricals, numerics).
    6. Detect & treat outliers in key numeric fields (Sales, Profit) using
       the IQR method, preserving the original values in *_Original columns
       for auditability.
    7. Enforce basic business-rule sanity checks (e.g. Quantity > 0).
    8. Write a human-readable cleaning report and the cleaned dataset.

Run:
    python -m src.data_cleaning
    (or: python src/data_cleaning.py  from the project root)
"""

from datetime import datetime

import numpy as np
import pandas as pd

from src import config
from src.utils import cap_outliers, get_logger, load_csv, save_csv

logger = get_logger(__name__)

EXPECTED_COLUMNS = [
    "Order_ID", "Order_Date", "Ship_Date", "Customer_ID", "Customer_Name",
    "Segment", "Region", "Product_ID", "Product_Category",
    "Product_Sub_Category", "Product_Name", "Sales", "Quantity", "Discount",
    "Profit", "Shipping_Cost", "Order_Priority", "Unit_Price", "Revenue",
]


def load_raw_data() -> pd.DataFrame:
    logger.info("Loading raw dataset from %s", config.RAW_SALES_FILE)
    df = load_csv(config.RAW_SALES_FILE, parse_dates=["Order_Date", "Ship_Date"])
    logger.info("Raw shape: %s", df.shape)
    return df


def validate_schema(df: pd.DataFrame) -> None:
    missing_cols = set(EXPECTED_COLUMNS) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Dataset is missing expected columns: {missing_cols}")
    logger.info("Schema validation passed (%d expected columns present).", len(EXPECTED_COLUMNS))


def report_missing_values(df: pd.DataFrame) -> pd.Series:
    missing = df.isnull().sum()
    missing = missing[missing > 0].sort_values(ascending=False)
    if missing.empty:
        logger.info("No missing values detected.")
    else:
        logger.info("Missing values found:\n%s", missing)
    return missing


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Impute / drop missing values using column-appropriate strategies."""
    df = df.copy()

    # Numeric columns critical to revenue math: drop rows where these are
    # missing since they cannot be safely imputed without distorting KPIs.
    critical_numeric = ["Sales", "Quantity", "Revenue"]
    before = len(df)
    df = df.dropna(subset=[c for c in critical_numeric if c in df.columns])
    dropped = before - len(df)
    if dropped:
        logger.info("Dropped %d rows missing critical numeric fields.", dropped)

    # Categorical columns: fill with explicit 'Unknown' rather than dropping,
    # so the rows remain usable for revenue/KPI analysis.
    categorical_fill = {
        "Segment": "Unknown",
        "Region": "Unknown",
        "Product_Category": "Unknown",
        "Product_Sub_Category": "Unknown",
        "Order_Priority": "Medium",
    }
    for col, fill_value in categorical_fill.items():
        if col in df.columns and df[col].isnull().any():
            n = df[col].isnull().sum()
            df[col] = df[col].fillna(fill_value)
            logger.info("Filled %d missing values in '%s' with '%s'.", n, col, fill_value)

    # Numeric columns that can reasonably be imputed with 0 / median:
    if "Discount" in df.columns:
        df["Discount"] = df["Discount"].fillna(0.0)
    if "Shipping_Cost" in df.columns:
        df["Shipping_Cost"] = df["Shipping_Cost"].fillna(df["Shipping_Cost"].median())
    if "Profit" in df.columns and df["Profit"].isnull().any():
        df["Profit"] = df["Profit"].fillna(df["Profit"].median())

    # Ship_Date: if missing, assume next day after order (typical for this business)
    if "Ship_Date" in df.columns and df["Ship_Date"].isnull().any():
        n = df["Ship_Date"].isnull().sum()
        df.loc[df["Ship_Date"].isnull(), "Ship_Date"] = (
            df.loc[df["Ship_Date"].isnull(), "Order_Date"] + pd.Timedelta(days=1)
        )
        logger.info("Imputed %d missing Ship_Date values as Order_Date + 1 day.", n)

    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates(subset=["Order_ID"], keep="first")
    df = df.drop_duplicates(keep="first")
    removed = before - len(df)
    logger.info("Removed %d duplicate rows.", removed)
    return df


def fix_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Order_Date"] = pd.to_datetime(df["Order_Date"], errors="coerce")
    df["Ship_Date"] = pd.to_datetime(df["Ship_Date"], errors="coerce")

    categorical_cols = [
        "Segment", "Region", "Product_Category", "Product_Sub_Category",
        "Order_Priority",
    ]
    for col in categorical_cols:
        if col in df.columns:
            df[col] = df[col].astype("category")

    numeric_cols = ["Sales", "Quantity", "Discount", "Profit", "Shipping_Cost",
                     "Unit_Price", "Revenue"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def enforce_business_rules(df: pd.DataFrame) -> pd.DataFrame:
    """Drop / correct rows that violate basic business logic."""
    before = len(df)

    # Quantity must be positive
    df = df[df["Quantity"] > 0]

    # Sales / Revenue must be non-negative
    df = df[(df["Sales"] >= 0) & (df["Revenue"] >= 0)]

    # Discount must be within [0, 1]
    df["Discount"] = df["Discount"].clip(lower=0.0, upper=1.0)

    # Ship_Date cannot precede Order_Date - if it does, set equal to Order_Date
    invalid_ship = df["Ship_Date"] < df["Order_Date"]
    if invalid_ship.any():
        logger.info("Fixed %d rows where Ship_Date preceded Order_Date.", invalid_ship.sum())
        df.loc[invalid_ship, "Ship_Date"] = df.loc[invalid_ship, "Order_Date"]

    removed = before - len(df)
    logger.info("Removed %d rows failing business-rule checks.", removed)
    return df


def treat_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Cap outliers in Sales and Profit using the IQR method.

    Original values are preserved in *_Original columns so the treatment is
    fully auditable and reversible.
    """
    df = df.copy()
    df["Sales_Original"] = df["Sales"]
    df["Profit_Original"] = df["Profit"]

    df["Sales"] = cap_outliers(df, "Sales")
    df["Profit"] = cap_outliers(df, "Profit")

    n_sales_capped = (df["Sales"] != df["Sales_Original"]).sum()
    n_profit_capped = (df["Profit"] != df["Profit_Original"]).sum()
    logger.info("Capped %d outlier values in Sales, %d in Profit (IQR method).",
                n_sales_capped, n_profit_capped)

    # Revenue should reflect the (possibly capped) Sales figure for downstream
    # KPI consistency, since in this dataset Revenue mirrors Sales at the
    # order-line level.
    df["Revenue"] = df["Sales"]
    return df


def write_cleaning_report(raw_shape, clean_shape, missing_before, out_path):
    lines = [
        "=" * 80,
        "DATA CLEANING REPORT",
        "=" * 80,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"Raw dataset shape:     {raw_shape[0]:,} rows x {raw_shape[1]} columns",
        f"Cleaned dataset shape: {clean_shape[0]:,} rows x {clean_shape[1]} columns",
        f"Rows removed:          {raw_shape[0] - clean_shape[0]:,} "
        f"({(raw_shape[0]-clean_shape[0]) / raw_shape[0] * 100:.2f}%)",
        "",
        "Missing values detected in raw data (before cleaning):",
    ]
    if missing_before.empty:
        lines.append("  None")
    else:
        for col, n in missing_before.items():
            lines.append(f"  - {col}: {n}")

    lines += [
        "",
        "Cleaning steps applied:",
        "  1. Schema validation against expected column set",
        "  2. Missing value imputation (categorical -> 'Unknown', numeric -> median/0)",
        "  3. Duplicate removal (by Order_ID and full-row duplicates)",
        "  4. Data type enforcement (datetime, category, numeric)",
        "  5. Business rule checks (Quantity > 0, non-negative Sales/Revenue, "
        "Discount in [0,1], Ship_Date >= Order_Date)",
        "  6. Outlier treatment on Sales & Profit via IQR capping "
        "(originals retained in *_Original columns)",
        "",
        "=" * 80,
    ]
    out_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Cleaning report written to %s", out_path)


def run():
    raw_df = load_raw_data()
    validate_schema(raw_df)
    missing_before = report_missing_values(raw_df)

    df = handle_missing_values(raw_df)
    df = remove_duplicates(df)
    df = fix_dtypes(df)
    df = enforce_business_rules(df)
    df = treat_outliers(df)

    df = df.reset_index(drop=True)

    save_csv(df, config.CLEAN_SALES_FILE)
    logger.info("Cleaned dataset saved to %s (shape=%s)", config.CLEAN_SALES_FILE, df.shape)

    report_path = config.REPORTS_DIR / "01_data_cleaning_report.txt"
    write_cleaning_report(raw_df.shape, df.shape, missing_before, report_path)

    return df


if __name__ == "__main__":
    run()
