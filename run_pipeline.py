"""
run_pipeline.py
-----------------
Single entry point that runs the entire analytics pipeline end-to-end, in
the correct dependency order. Equivalent to running each src/ module's
`run()` function manually, but convenient for a fresh clone / CI job.

Usage:
    python run_pipeline.py                  # run everything
    python run_pipeline.py --skip-ml        # skip the ML modules (faster)
"""

import argparse
import time

from src import (
    clv_analysis,
    cohort_analysis,
    customer_segmentation,
    data_cleaning,
    eda,
    feature_engineering,
    generate_kpi_report,
    rfm_analysis,
    sales_forecasting,
)
from src.ml import churn_prediction, sales_prediction
from src.utils import get_logger

logger = get_logger("run_pipeline")

STAGES = [
    ("1/10  Data Cleaning", data_cleaning.run),
    ("2/10  Feature Engineering", feature_engineering.run),
    ("3/10  Exploratory Data Analysis", eda.run),
    ("4/10  RFM Analysis", rfm_analysis.run),
    ("5/10  Customer Lifetime Value", clv_analysis.run),
    ("6/10  Customer Segmentation (K-Means)", customer_segmentation.run),
    ("7/10  Cohort Retention Analysis", cohort_analysis.run),
    ("8/10  Sales Forecasting", sales_forecasting.run),
    ("9/10  KPI & Executive Report", generate_kpi_report.run),
]

ML_STAGES = [
    ("10a/10  Churn Prediction Model", churn_prediction.run),
    ("10b/10  Sales Prediction Model", sales_prediction.run),
]


def main():
    parser = argparse.ArgumentParser(description="Run the Retail & Marketing Analytics pipeline.")
    parser.add_argument("--skip-ml", action="store_true", help="Skip the two ML modeling stages.")
    args = parser.parse_args()

    stages = STAGES + ([] if args.skip_ml else ML_STAGES)

    logger.info("=" * 80)
    logger.info("STARTING RETAIL & MARKETING ANALYTICS PIPELINE (%d stages)", len(stages))
    logger.info("=" * 80)

    start = time.time()
    for label, fn in stages:
        stage_start = time.time()
        logger.info(">>> %s", label)
        fn()
        logger.info("<<< %s complete (%.1fs)", label, time.time() - stage_start)

    logger.info("=" * 80)
    logger.info("PIPELINE COMPLETE in %.1fs. See data/processed/, reports/, images/, models/", 
                time.time() - start)
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
