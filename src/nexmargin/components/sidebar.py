"""Sidebar navigation and the shared filter bar."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from .. import analytics as A

PAGES = [("Overview", ":material/dashboard:"), ("Explore", ":material/query_stats:"),
         ("AI Copilot", ":material/auto_awesome:"), ("Reports", ":material/description:")]


def _go(page: str) -> None:
    st.session_state["page"] = page


def render_sidebar(meta: str, ai_ready: bool) -> str:
    st.session_state.setdefault("page", PAGES[0][0])
    with st.sidebar:
        st.markdown('<div class="nx-brand"><div class="nx-logo">N</div><div><div class="nx-brand-name">NexMargin</div>'
                    '<div class="nx-brand-tag">Retail profit intelligence</div></div></div>', unsafe_allow_html=True)
        for name, icon in PAGES:
            active = st.session_state["page"] == name
            st.button(name, icon=icon, key=f"nav_{name}", type="primary" if active else "secondary",
                      width="stretch", on_click=_go, args=(name,))
        st.markdown("<div style='height:2.2rem'></div>", unsafe_allow_html=True)
        status = ('<span class="nx-status on"><span class="nx-dot"></span>AI connected</span>' if ai_ready
                  else '<span class="nx-status off"><span class="nx-dot"></span>Demo mode (no API key)</span>')
        st.markdown(status, unsafe_allow_html=True)
        st.markdown(f'<div class="nx-side-note" style="margin-top:.8rem">{meta}</div>', unsafe_allow_html=True)
    return st.session_state["page"]


@dataclass
class Filters:
    df: pd.DataFrame            # fully filtered
    df_scope: pd.DataFrame      # filtered except for the date range (used for period comparisons)
    start: pd.Timestamp
    end: pd.Timestamp
    data_min: pd.Timestamp
    scope: str                  # human-readable description of the filters


def filter_bar(df_all: pd.DataFrame, key: str, categories: bool = False, segments: bool = False) -> Filters:
    """Date range + region (+ optional category and segment). Empty multi-selects mean 'all'."""
    dmin, dmax = df_all["order_date"].min().date(), df_all["order_date"].max().date()
    widths = [1.5, 1.4] + ([1.2] if categories else []) + ([1.2] if segments else [])
    cols = st.columns(widths)
    with cols[0]:
        rng = st.date_input("Date range", value=(dmin, dmax), min_value=dmin, max_value=dmax, key=f"{key}_date", format="YYYY-MM-DD")
    i = 1
    with cols[i]:
        regions = st.multiselect("Region", sorted(df_all["region"].unique()), key=f"{key}_region", placeholder="All regions")
    cats, segs = [], []
    if categories:
        i += 1
        with cols[i]:
            cats = st.multiselect("Category", sorted(df_all["category"].unique()), key=f"{key}_cat", placeholder="All categories")
    if segments:
        i += 1
        with cols[i]:
            segs = st.multiselect("Customer segment", sorted(df_all["segment"].unique()), key=f"{key}_seg", placeholder="All segments")

    if not isinstance(rng, (tuple, list)) or len(rng) != 2:
        st.info("Pick an end date to complete the range.")
        st.stop()
    start, end = pd.Timestamp(rng[0]), pd.Timestamp(rng[1])
    scope_df = A.apply_filters(df_all, regions=regions, categories=cats, segments=segs)
    filtered = A.apply_filters(scope_df, start, end)
    scope = (f"{start:%d %b %Y} - {end:%d %b %Y} | Regions: {', '.join(regions) or 'all'}"
             + (f" | Categories: {', '.join(cats) or 'all'}" if categories else "")
             + (f" | Segments: {', '.join(segs) or 'all'}" if segments else ""))
    return Filters(filtered, scope_df, start, end, df_all["order_date"].min(), scope)
