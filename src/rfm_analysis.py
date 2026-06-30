"""
04_rfm_analysis.py
-------------------
Stage 4 of the analytics pipeline: RFM (Recency, Frequency, Monetary) Analysis.

For each customer, computes:
    - Recency:  days since their most recent purchase (relative to the
                most recent date in the whole dataset - a "snapshot" analysis,
                standard practice for non-streaming historical datasets).
    - Frequency: number of distinct orders placed.
    - Monetary:  total revenue generated.

Each metric is scored 1-5 using quintiles, combined into an RFM_Score, and
mapped to a named business segment (Champions, Loyal Customers, At Risk,
etc.) using a rule-based lookup that mirrors common industry RFM playbooks
(e.g. the classic 11-segment RFM heatmap used by marketing teams).

Run:
    python -m src.rfm_analysis
"""

import pandas as pd

from src import config
from src.utils import get_logger, load_csv, save_csv

logger = get_logger(__name__)


def compute_rfm_table(df: pd.DataFrame) -> pd.DataFrame:
    snapshot_date = df["Order_Date"].max() + pd.Timedelta(days=1)
    logger.info("Snapshot date for recency calculation: %s", snapshot_date.date())

    rfm = df.groupby("Customer_ID").agg(
        Recency=("Order_Date", lambda x: (snapshot_date - x.max()).days),
        Frequency=("Order_ID", "nunique"),
        Monetary=("Revenue", "sum"),
    ).reset_index()

    return rfm


def score_rfm(rfm: pd.DataFrame, quantiles: int = config.RFM_QUANTILES) -> pd.DataFrame:
    rfm = rfm.copy()

    # Recency: LOWER is better -> reverse labels (5 = most recent)
    rfm["R_Score"] = pd.qcut(
        rfm["Recency"].rank(method="first"), quantiles, labels=list(range(quantiles, 0, -1))
    ).astype(int)

    # Frequency & Monetary: HIGHER is better
    rfm["F_Score"] = pd.qcut(
        rfm["Frequency"].rank(method="first"), quantiles, labels=list(range(1, quantiles + 1))
    ).astype(int)
    rfm["M_Score"] = pd.qcut(
        rfm["Monetary"].rank(method="first"), quantiles, labels=list(range(1, quantiles + 1))
    ).astype(int)

    rfm["RFM_Score"] = (
        rfm["R_Score"].astype(str) + rfm["F_Score"].astype(str) + rfm["M_Score"].astype(str)
    )
    rfm["RFM_Score_Numeric"] = rfm[["R_Score", "F_Score", "M_Score"]].mean(axis=1)
    return rfm


def assign_segment(row) -> str:
    """Map (R, F, M) scores to a named marketing segment.

    This follows the widely-used RFM segmentation heuristic popularized by
    retail CRM playbooks (e.g. Putler / KISSmetrics style RFM grids).
    """
    r, f, m = row["R_Score"], row["F_Score"], row["M_Score"]

    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    if r >= 3 and f >= 3 and m >= 3:
        return "Loyal Customers"
    if r >= 4 and f <= 2:
        return "New Customers"
    if r >= 3 and f <= 2 and m <= 2:
        return "Promising"
    if r == 3 and f == 3:
        return "Need Attention"
    if r <= 2 and f >= 3 and m >= 3:
        return "At Risk"
    if r <= 2 and f >= 4 and m >= 4:
        return "Cannot Lose Them"
    if r <= 2 and f <= 2 and m <= 2:
        return "Lost"
    if r <= 2:
        return "About to Sleep"
    return "Need Attention"


def run() -> pd.DataFrame:
    df = load_csv(config.FEATURED_SALES_FILE, parse_dates=["Order_Date", "Ship_Date"])

    rfm = compute_rfm_table(df)
    rfm = score_rfm(rfm)
    rfm["Customer_Segment"] = rfm.apply(assign_segment, axis=1)

    logger.info("RFM segment distribution:\n%s", rfm["Customer_Segment"].value_counts())

    save_csv(rfm, config.RFM_FILE)
    logger.info("RFM analysis saved to %s (n=%d customers)", config.RFM_FILE, len(rfm))
    return rfm


if __name__ == "__main__":
    run()
