"""Overview: the executive dashboard."""
from __future__ import annotations

import streamlit as st

from .. import analytics as A
from .. import metrics
from ..components import charts
from ..components.kpi_cards import render_kpis
from ..components.sidebar import filter_bar
from ..components.styling import card, card_header, empty_state, insight_html, legend, page_header

PLOT = dict(config=charts.PLOT_CONFIG, theme=None, width="stretch")


def render(df_all) -> None:
    page_header("Overview", "Revenue tells you how much you sell. Profit tells you how much you keep.")
    f = filter_bar(df_all, "ov")
    if f.df.empty:
        return empty_state()

    comparison = A.compare_kpis(f.df_scope, f.start, f.end, f.data_min)
    render_kpis(comparison, metrics.monthly_series(f.df))

    left, right = st.columns([2.2, 1])
    with left, card("trend"):
        card_header("Revenue vs profit", "Monthly trend for the selected period")
        st.plotly_chart(charts.trend_chart(A.monthly_trend(f.df)), key="chart_ov_trend", **PLOT)
    with right, card("insights"):
        card_header("Business insights", "What stands out in this selection")
        insights = A.business_insights(f.df, limit=3)
        if insights:
            st.markdown("".join(insight_html(i) for i in insights), unsafe_allow_html=True)
        else:
            st.caption("No notable patterns in this selection.")

    st.write("")
    c1, c2 = st.columns([1.25, 1])
    with c1, card("category"):
        card_header("Category profitability", "Profit margin by sub-category; dotted line is the overall margin")
        legend([("Profitable", charts.GREEN), ("Low margin", charts.AMBER), ("Loss-making", charts.RED)])
        sub = A.subcategory_margin(f.df)
        st.plotly_chart(charts.category_bar(sub, comparison["current"]["margin_pct"]), key="chart_ov_cat", **PLOT)
    with c2, card("region"):
        card_header("Regional performance", "Revenue and profit by region")
        st.plotly_chart(charts.region_chart(A.region_performance(f.df)), key="chart_ov_region", **PLOT)
