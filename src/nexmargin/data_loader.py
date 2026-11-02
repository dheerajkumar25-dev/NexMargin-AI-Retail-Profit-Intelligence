"""Load raw data, run the cleaning pipeline, and read the processed dataset."""
from __future__ import annotations

import json
import urllib.request

import pandas as pd

from . import config
from .preprocessing import clean

DATE_COLUMNS = ["order_date", "ship_date", "order_month"]


def download_raw(force: bool = False) -> None:
    """Download the raw CSV if it is not already in data/raw."""
    if config.RAW_FILE.exists() and not force:
        return
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(config.RAW_SOURCE_URL, config.RAW_FILE)


def load_raw() -> pd.DataFrame:
    if not config.RAW_FILE.exists():
        download_raw()
    return pd.read_csv(config.RAW_FILE, encoding="latin1")  # export is not UTF-8


def build_processed() -> dict:
    """Raw -> clean CSV + quality report. Safe to re-run; raw data is never modified."""
    df, report = clean(load_raw())
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(config.PROCESSED_FILE, index=False, encoding="utf-8")
    config.QUALITY_REPORT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def load_processed() -> pd.DataFrame:
    """Return the cleaned dataset, building it on first use."""
    if not config.PROCESSED_FILE.exists():
        build_processed()
    df = pd.read_csv(config.PROCESSED_FILE, parse_dates=DATE_COLUMNS)
    df["is_loss"] = df["is_loss"].astype(bool)
    df["is_profit_outlier"] = df["is_profit_outlier"].astype(bool)
    return df


def load_quality_report() -> dict:
    if not config.QUALITY_REPORT_FILE.exists():
        build_processed()
    return json.loads(config.QUALITY_REPORT_FILE.read_text(encoding="utf-8"))
