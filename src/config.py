"""
config.py
----------
Centralized configuration for the Retail & Marketing Analytics pipeline.

All paths are resolved relative to the project root so every script works
regardless of the directory it is executed from (as long as the repo
structure is preserved).

Author: Data Analytics Team
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

REPORTS_DIR = PROJECT_ROOT / "reports"
IMAGES_DIR = PROJECT_ROOT / "images"
EDA_IMAGES_DIR = IMAGES_DIR / "eda"
MODELS_DIR = PROJECT_ROOT / "models"
SQL_DIR = PROJECT_ROOT / "sql"

# Raw / processed file names
RAW_SALES_FILE = RAW_DATA_DIR / "retail_sales_data.csv"
CLEAN_SALES_FILE = PROCESSED_DATA_DIR / "retail_sales_clean.csv"
FEATURED_SALES_FILE = PROCESSED_DATA_DIR / "cleaned_retail_sales.csv"

RFM_FILE = PROCESSED_DATA_DIR / "rfm_analysis.csv"
CLV_FILE = PROCESSED_DATA_DIR / "customer_clv.csv"
SEGMENTS_FILE = PROCESSED_DATA_DIR / "customer_segments.csv"
MONTHLY_KPI_FILE = PROCESSED_DATA_DIR / "monthly_kpis.csv"
CHURN_PRED_FILE = PROCESSED_DATA_DIR / "churn_predictions.csv"
FORECAST_FILE = PROCESSED_DATA_DIR / "sales_forecast.csv"

# Ensure required directories exist (idempotent, safe to import anywhere)
for _dir in [
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    REPORTS_DIR,
    IMAGES_DIR,
    EDA_IMAGES_DIR,
    MODELS_DIR,
]:
    _dir.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# BUSINESS / ANALYTICS CONSTANTS
# ---------------------------------------------------------------------------
# Customer Acquisition Cost assumption used for CLV:CAC ratio (industry
# benchmark placeholder — replace with actual blended CAC from finance/marketing).
CUSTOMER_ACQUISITION_COST = 50.0

# A customer is considered "churned" if they have not purchased in this many
# days, relative to the most recent date in the dataset (snapshot analysis).
CHURN_RECENCY_THRESHOLD_DAYS = 90

# RFM scoring uses quintiles (1-5) by default.
RFM_QUANTILES = 5

# KMeans clustering
KMEANS_RANDOM_STATE = 42
KMEANS_MAX_CLUSTERS_TO_TEST = 10
KMEANS_N_CLUSTERS = 4  # chosen via elbow/silhouette analysis - see notebooks

# Forecasting
FORECAST_HORIZON_MONTHS = 3
TRAIN_TEST_SPLIT_DATE_HOLDOUT_MONTHS = 3  # last N months held out for testing

# CLV projection horizon: CLV_Simple projects each customer's OBSERVED
# purchase frequency forward over this many years (industry-standard
# assumption for a "simple" CLV estimate; replace with a cohort-specific
# average tenure if you have multi-year history). NOTE: this must be a
# fixed constant, not the customer's own observed lifespan - using the
# observed lifespan in both the frequency denominator and the projection
# multiplier cancels out algebraically and collapses CLV_Simple back to
# raw historical revenue, which is a common analyst mistake worth avoiding.
CLV_PROJECTION_YEARS = 3

# Plot style
PLOT_STYLE = "seaborn-v0_8-whitegrid"
FIGURE_DPI = 150
PALETTE = "viridis"

RANDOM_STATE = 42
