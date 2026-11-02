"""Reports: executive summary and exports."""
from __future__ import annotations

import streamlit as st

from .. import ai_copilot as ai
from .. import analytics as A
from .. import metrics
from ..components import charts, tables
from ..components.kpi_cards import render_kpis
from ..components.sidebar import filter_bar
from ..components.styling import card, card_header, empty_state, insight_html, page_header
from ..report_generator import build_pdf, filtered_csv, summary_zip

PLOT = dict(config=charts.PLOT_CONFIG, theme=None, width="stretch")


@st.cache_data(show_spinner=False)
def _pdf(df, scope, text, mode):
    return build_pdf(df, scope, text, mode)


@st.cache_resource(show_spinner=False)
def _llm():
    return ai.make_groq_llm()


def render(df_all) -> None:
    page_header("Reports", "A shareable summary of the selected period, with exports.")
    f = filter_bar(df_all, "rp")
    if f.df.empty:
        return empty_state()
    render_kpis(A.compare_kpis(f.df_scope, f.start, f.end, f.data_min), compact=True)
    st.write("")

    # Executive summary: rule-based by default; AI-written on request (and number-verified).
    text, mode = ai.executive_summary(f.df, f.scope, None)
    stored = st.session_state.get("rp_ai_summary")
    if stored and stored["scope"] == f.scope:
        text, mode = stored["text"], stored["mode"]

    main, side = st.columns([2.2, 1])
    with main:
        with card("summary"):
            card_header("Executive summary", f.scope)
            label = "AI-generated" if mode == "AI explanation" else "Auto-generated (rule-based)"
            st.markdown(f'<span class="nx-badge {"" if mode == "AI explanation" else "muted"}">{label}</span>', unsafe_allow_html=True)
            st.markdown(text)
            llm = _llm()
            if st.button("Generate AI summary", key="rp_ai", disabled=llm is None,
                         help="Requires GROQ_API_KEY in .env" if llm is None else "Rewrites the summary with the AI model; numbers are verified."):
                with st.spinner("Writing summary..."):
                    t, m = ai.executive_summary(f.df, f.scope, llm)
                st.session_state["rp_ai_summary"] = {"scope": f.scope, "text": t, "mode": m}
                st.rerun()
        st.write("")
        with card("rev"):
            card_header("Revenue summary", "Monthly revenue and profit")
            st.plotly_chart(charts.trend_chart(A.monthly_trend(f.df)), key="chart_rp_trend", **PLOT)
        st.write("")
        with card("cats"):
            card_header("Top-performing categories")
            tables.show(metrics.group_summary(f.df, "category").sort_values("profit", ascending=False)
                        [["category", "revenue", "profit", "margin_pct", "profit_share_pct"]])
        st.write("")
        with card("regs"):
            card_header("Regional insights")
            tables.show(metrics.group_summary(f.df, "region").sort_values("profit", ascending=False)
                        [["region", "revenue", "profit", "margin_pct", "orders"]])
    with side:
        with card("export"):
            card_header("Export", "Files reflect the filters above")
            st.download_button("Download PDF report", _pdf(f.df, f.scope, text, mode), "nexmargin_report.pdf", "application/pdf",
                               key="rp_pdf", type="primary", width="stretch")
            st.download_button("Filtered data (CSV)", filtered_csv(f.df), "nexmargin_filtered_orders.csv", "text/csv", key="rp_csv", width="stretch")
            st.download_button("Summary tables (ZIP)", summary_zip(f.df), "nexmargin_summaries.zip", "application/zip", key="rp_zip", width="stretch")
        st.write("")
        with card("obs"):
            card_header("Business observations")
            ins = A.business_insights(f.df, limit=3)
            st.markdown("".join(insight_html(i) for i in ins) if ins else "No notable patterns in this selection.", unsafe_allow_html=True)
