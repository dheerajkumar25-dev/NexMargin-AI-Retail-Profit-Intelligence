"""KPI cards with honest period-over-period deltas and optional sparklines."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from ..formatting import fmt_count, fmt_money, fmt_pct

INDIGO = "#4F46E5"


def sparkline(values, width: int = 92, height: int = 34) -> str:
    vals = [float(v) for v in values if pd.notna(v)]
    if len(vals) < 3:
        return ""
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1.0
    pts = [(i / (len(vals) - 1) * (width - 4) + 2, height - 3 - (v - lo) / span * (height - 8)) for i, v in enumerate(vals)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"2,{height} {line} {width - 2},{height}"
    return (f'<svg class="nx-spark" width="{width}" height="{height}" viewBox="0 0 {width} {height}" aria-hidden="true">'
            f'<polygon points="{area}" fill="{INDIGO}" fill-opacity=".09"/>'
            f'<polyline points="{line}" fill="none" stroke="{INDIGO}" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/></svg>')


def _delta_html(change, unit: str, title: str) -> str:
    if change is None:
        return '<span class="nx-delta none">No prior period</span>'
    if abs(change) < 0.05:
        return f'<span class="nx-delta flat" title="{title}">0.0{unit}</span>'
    cls, arrow = ("up", "▲") if change > 0 else ("down", "▼")
    return f'<span class="nx-delta {cls}" title="{title}">{arrow} {abs(change):.1f}{unit}</span>'


def render_kpis(comparison: dict, monthly: pd.DataFrame | None = None, compact: bool = False) -> None:
    """Four KPI cards. `comparison` comes from analytics.compare_kpis."""
    cur, ch = comparison["current"], comparison["changes"]
    pr = comparison.get("previous_range")
    title = f"vs {pr[0]:%d %b %Y} to {pr[1]:%d %b %Y}" if pr else ""
    cards = [
        ("Total revenue", fmt_money(cur["revenue"]), _delta_html(ch.get("revenue"), "%", title), "revenue"),
        ("Total profit", fmt_money(cur["profit"]), _delta_html(ch.get("profit"), "%", title), "profit"),
        ("Profit margin", fmt_pct(cur["margin_pct"]), _delta_html(ch.get("margin_pp"), " pp", title), "margin_pct"),
        ("Total orders", fmt_count(cur["orders"]), _delta_html(ch.get("orders"), "%", title), "orders"),
    ]
    cols = st.columns(4)
    for col, (label, value, delta, series) in zip(cols, cards):
        spark = "" if (compact or monthly is None or monthly.empty) else sparkline(monthly[series])
        vs = '<span title="Compared with the equal-length period immediately before">vs prior period</span>' if pr else ""
        col.markdown(f'<div class="nx-kpi{" compact" if compact else ""}">{spark}<div class="nx-kpi-label">{label}</div>'
                     f'<div class="nx-kpi-value">{value}</div><div class="nx-kpi-foot">{delta}{vs}</div></div>', unsafe_allow_html=True)
    if not compact:
        if pr:
            st.caption(f"Changes compare with {pr[0]:%d %b %Y} - {pr[1]:%d %b %Y}. Margin change is in percentage points (pp).")
        else:
            st.caption("No prior-period comparison: the selection has no equal-length window of earlier data to compare against.")
