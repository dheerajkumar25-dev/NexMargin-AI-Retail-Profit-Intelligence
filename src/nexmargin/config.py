
"""Central configuration: paths, dataset source, and environment settings."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
RAW_FILE = RAW_DIR / "Sample - Superstore.csv"
PROCESSED_FILE = PROCESSED_DIR / "orders_clean.csv"
QUALITY_REPORT_FILE = PROCESSED_DIR / "data_quality_report.json"

# Original: Kaggle "Superstore Dataset" (vivek468).
# Licence not verified - see docs/data_dictionary.md.
# This GitHub mirror is used as a convenient download location.
RAW_SOURCE_URL = (
    "https://raw.githubusercontent.com/Ayon-coder/FUTURE_ML_01/main/Sample%20-%20Superstore.csv"
)

# Dataset currency is US dollars.
CURRENCY_SYMBOL = os.getenv("NEXMARGIN_CURRENCY", "$")


def get_setting(name: str, default: str = "") -> str:
    """Read settings from environment variables or Streamlit Cloud Secrets."""

    # First check local environment variables and .env.
    value = os.getenv(name, "").strip()

    if value:
        return value

    # Then check Streamlit Community Cloud Secrets.
    try:
        import streamlit as st

        value = str(st.secrets.get(name, default)).strip()
        return value
    except Exception:
        return default


GROQ_API_KEY = get_setting("GROQ_API_KEY")
GROQ_MODEL = get_setting(
    "GROQ_MODEL",
    "llama-3.3-70b-versatile"
)
