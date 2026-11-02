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

# Original: Kaggle "Superstore Dataset" (vivek468). Licence not verified - see docs/data_dictionary.md.
# This GitHub mirror is used only as a convenient download location.
RAW_SOURCE_URL = (
    "https://raw.githubusercontent.com/Ayon-coder/FUTURE_ML_01/main/Sample%20-%20Superstore.csv"
)

# The dataset is in US dollars. We do not relabel it as rupees.
CURRENCY_SYMBOL = os.getenv("NEXMARGIN_CURRENCY", "$")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
