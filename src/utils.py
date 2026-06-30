"""
utils.py
--------
Shared helper functions used across the analytics pipeline:
- consistent logging
- safe CSV I/O
- common plotting setup
- small numerical helpers (IQR bounds, currency formatting)

Keeping these in one place avoids duplicating boilerplate across every
script in src/ and src/ml/.
"""

import logging
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src import config


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger that prints timestamped messages to stdout."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def load_csv(path: Path, parse_dates=None, **kwargs) -> pd.DataFrame:
    """Load a CSV file with a friendly error if it doesn't exist yet."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Expected input file not found: {path}\n"
            f"Did you run the upstream pipeline step first? "
            f"(see README.md -> 'How to Run the Pipeline')"
        )
    return pd.read_csv(path, parse_dates=parse_dates, **kwargs)


def save_csv(df: pd.DataFrame, path: Path, index: bool = False) -> None:
    """Save a DataFrame to CSV, creating parent directories if needed."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=index)


def iqr_bounds(series: pd.Series, k: float = 1.5):
    """Return (lower_bound, upper_bound) for outlier capping using the IQR rule."""
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    return q1 - k * iqr, q3 + k * iqr


def cap_outliers(df: pd.DataFrame, column: str, k: float = 1.5) -> pd.Series:
    """Cap (winsorize) outliers in a column to the IQR bounds and return the series."""
    lower, upper = iqr_bounds(df[column], k=k)
    return df[column].clip(lower=lower, upper=upper)


def setup_plot_style():
    """Apply a consistent, presentation-ready style to all matplotlib/seaborn charts."""
    try:
        plt.style.use(config.PLOT_STYLE)
    except OSError:
        plt.style.use("default")
    plt.rcParams["figure.dpi"] = config.FIGURE_DPI
    plt.rcParams["axes.titlesize"] = 14
    plt.rcParams["axes.titleweight"] = "bold"
    plt.rcParams["axes.labelsize"] = 11
    plt.rcParams["figure.facecolor"] = "white"


def save_fig(fig, filename: str, directory: Path = None):
    """Save a matplotlib figure into images/eda (or a custom directory) as PNG."""
    directory = Path(directory) if directory else config.EDA_IMAGES_DIR
    directory.mkdir(parents=True, exist_ok=True)
    out_path = directory / filename
    fig.savefig(out_path, dpi=config.FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    return out_path


def fmt_currency(value: float) -> str:
    """Format a number as currency for printed reports, e.g. 1234.5 -> '$1,234.50'."""
    return f"${value:,.2f}"


def fmt_pct(value: float, decimals: int = 2) -> str:
    """Format a number as a percentage string, e.g. 12.345 -> '12.35%'."""
    return f"{value:.{decimals}f}%"
