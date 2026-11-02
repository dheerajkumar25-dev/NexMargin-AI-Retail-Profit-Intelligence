"""NexMargin - AI-powered retail profit intelligence.  Run: streamlit run app.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import streamlit as st  # noqa: E402

st.set_page_config(page_title="NexMargin", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

from nexmargin import config  # noqa: E402
from nexmargin.components.sidebar import render_sidebar  # noqa: E402
from nexmargin.components.styling import inject_css  # noqa: E402
from nexmargin.data_loader import load_processed  # noqa: E402
from nexmargin.pages import copilot, explore, overview, reports  # noqa: E402

PAGE_RENDERERS = {"Overview": overview.render, "Explore": explore.render, "AI Copilot": copilot.render, "Reports": reports.render}


@st.cache_data(show_spinner="Loading data...")
def get_data():
    return load_processed()


def main() -> None:
    inject_css()
    try:
        df = get_data()
    except Exception as exc:  # noqa: BLE001 - show a fix, not a stack trace
        render_sidebar("", bool(config.GROQ_API_KEY))
        st.error("Could not load the dataset.")
        st.markdown(f"Run `python scripts/build_data.py` to download and process it. Details: `{type(exc).__name__}: {exc}`")
        return
    meta = f"Superstore sample data<br>{len(df):,} order lines · {df['order_date'].min():%b %Y} to {df['order_date'].max():%b %Y}<br>Amounts in US dollars"
    page = render_sidebar(meta, bool(config.GROQ_API_KEY))
    PAGE_RENDERERS[page](df)


main()
