
"""Explore: interactive analytics workspace."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from .. import analytics as A
from .. import metrics, segmentation
from ..components import charts, tables
from ..components.kpi_cards import render_kpis
from ..components.sidebar import filter_bar
from ..components.styling import card, card_header, empty_state, stat
from ..components.styling import page_header
from ..forecasting import LIMITATIONS, MIN_MONTHS, forecast_revenue
from ..formatting import fmt_money, fmt_pct
from ..report_generator import EXPORT_COLUMNS, filtered_csv

PLOT = dict(config=charts.PLOT_CONFIG, theme=None, width="stretch")


@st.cache_data(show_spinner=False)
def _rfm(df):
    return segmentation.rfm_table(df)


@st.cache_data(show_spinner=False)
def _forecast(monthly, horizon):
    return forecast_revenue(monthly, horizon=horizon)


def _products(df) -> None:
    c1, c2 = st.columns(2)

    with c1, card("p_rev"):
        card_header("Top 10 products by revenue")
        st.plotly_chart(
            charts.hbar(
                A.top_products_by_revenue(df, 10),
                "product_name",
                "revenue",
            ),
            key="chart_ex_p_rev",
            **PLOT,
        )

    with c2, card("p_profit"):
        card_header("Top 10 products by profit")
        st.plotly_chart(
            charts.hbar(
                A.top_products_by_profit(df, 10),
                "product_name",
                "profit",
                color=charts.GREEN,
            ),
            key="chart_ex_p_profit",
            **PLOT,
        )

    st.write("")

    c3, c4 = st.columns(2)

    with c3, card("p_low"):
        card_header(
            "Lowest-margin products",
            "Products with enough revenue to matter",
        )

        min_rev = st.slider(
            "Minimum product revenue",
            0,
            5000,
            500,
            100,
            key="ex_minrev",
        )

        low = A.lowest_margin_products(df, 10, float(min_rev))

        if low.empty:
            st.caption("No products meet that revenue threshold.")
        else:
            st.plotly_chart(
                charts.hbar(
                    low,
                    "product_name",
                    "margin_pct",
                    kind="pct",
                ),
                key="chart_ex_p_low",
                **PLOT,
            )

    with c4, card("p_contrib"):
        card_header(
            "Product contribution",
            "How concentrated is the business?",
        )

        metric = st.radio(
            "Measure",
            ["Revenue", "Profit"],
            horizontal=True,
            key="ex_contrib",
            label_visibility="collapsed",
        )

        curve = A.contribution_curve(
            df,
            "sales" if metric == "Revenue" else "profit",
        )

        hit = A.products_for_share(curve)

        if hit:
            st.markdown(
                f"**{hit[0]:,} products ({hit[1]:.0f}%)** "
                f"generate 80% of {metric.lower()}."
            )

            st.plotly_chart(
                charts.pareto_chart(curve),
                key="chart_ex_pareto",
                **PLOT,
            )
        else:
            st.caption(
                "Not enough positive values to compute contribution."
            )

    # Product Performance Matrix
    st.write("")

    with card("p_matrix"):
        card_header(
            "Product Performance Matrix",
            "Classify products using revenue and profit margin.",
        )

        matrix = A.product_performance_matrix(df)

        if matrix.empty:
            st.caption("No product performance data available.")

        else:
            counts = matrix["performance"].value_counts()

            summary_cols = st.columns(4)

            categories = [
                "High Performer",
                "Revenue Driver",
                "Hidden Gem",
                "Underperformer",
            ]

            for col, category in zip(summary_cols, categories):
                with col:
                    stat(
                        category,
                        f"{counts.get(category, 0):,}",
                    )

            st.write("")

            display_cols = [
                "product_name",
                "category",
                "revenue",
                "profit",
                "margin_pct",
                "performance",
            ]

            tables.show(
                matrix[display_cols],
                height=350,
            )


def _customers(df) -> None:
    summ = A.customer_orders_summary(df)

    with card("c_stats"):
        a, b, c, d = st.columns(4)

        with a:
            stat("Customers", f"{summ['customers']:,}")

        with b:
            stat("Repeat customers", fmt_pct(summ["repeat_rate_pct"]))

        with c:
            stat("Average order value", fmt_money(summ["aov"]))

        with d:
            stat(
                "Orders per customer",
                f"{summ['orders_per_customer']:.1f}"
                if summ["orders_per_customer"]
                else "n/a",
            )

    st.write("")

    c1, c2 = st.columns(2)

    with c1, card("c_top"):
        card_header("Top 10 customers by revenue")

        conc = A.customer_concentration(df)

        if conc is not None:
            st.caption(
                f"The top 10% of customers account for {fmt_pct(conc)} of revenue."
            )

        st.plotly_chart(
            charts.hbar(
                A.top_customers(df, 10),
                "customer_name",
                "revenue",
            ),
            key="chart_ex_c_top",
            **PLOT,
        )

    with c2, card("c_freq"):
        card_header(
            "Purchase frequency",
            "Customers by number of orders placed",
        )

        st.plotly_chart(
            charts.count_bar(
                A.purchase_frequency(df),
                "frequency_band",
                "customers",
            ),
            key="chart_ex_c_freq",
            **PLOT,
        )

    st.write("")

    rfm = _rfm(df)
    summary = segmentation.segment_summary(rfm)

    c3, c4 = st.columns([1, 1.15])

    with c3, card("c_rfm"):
        card_header(
            "Customer segments (RFM)",
            "Scored on recency, frequency and spend",
        )

        st.plotly_chart(
            charts.rfm_chart(summary),
            key="chart_ex_c_rfm",
            **PLOT,
        )

    with c4, card("c_rfm_t"):
        card_header(
            "Segment value",
            "Revenue and profit by RFM segment",
        )

        tables.show(
            summary[
                [
                    "segment",
                    "customers",
                    "revenue",
                    "profit",
                    "avg_recency_days",
                ]
            ],
            height=250,
        )

        st.caption(
            "Champions: recent, frequent, high spend. "
            "At Risk: valuable but lapsing. "
            "Method in docs/methodology.md."
        )

    st.write("")

    c5, c6 = st.columns(2)

    with c5, card("c_aov"):
        card_header("Average order value by customer segment")

        seg = metrics.group_summary(
            df,
            "segment",
        ).sort_values("aov", ascending=False)

        st.plotly_chart(
            charts.hbar(
                seg,
                "segment",
                "aov",
                height=200,
            ),
            key="chart_ex_c_aov",
            **PLOT,
        )

    with c6, card("c_ret"):
        card_header(
            "Customer retention",
            "Of customers active in a year, the share who ordered again the next year",
        )

        ret = metrics.annual_retention(df)

        if ret.empty:
            st.caption(
                "Retention needs at least two consecutive years in the selection."
            )
        else:
            st.plotly_chart(
                charts.retention_chart(ret),
                key="chart_ex_c_ret",
                **PLOT,
            )


def _discounts(df) -> None:
    leak = A.discount_leakage(df)

    if leak["lines"] and leak["profit"] < 0:
        st.markdown(
            f'<div class="nx-callout"><b>Profit leakage:</b> '
            f'lines discounted {leak["threshold_pct"]:.0f}%+ generated '
            f'{fmt_money(leak["revenue"])} '
            f'({fmt_pct(leak["revenue_share_pct"])} of revenue) '
            f'and a profit of <b>{fmt_money(leak["profit"])}</b>. '
            f'{fmt_pct(leak["loss_line_pct"], 0)} of those lines lose money.'
            f'</div>',
            unsafe_allow_html=True,
        )

    elif leak["lines"]:
        st.markdown(
            f'<div class="nx-callout good">Lines discounted '
            f'{leak["threshold_pct"]:.0f}%+ are still profitable here '
            f'({fmt_money(leak["profit"])} profit, '
            f'{fmt_pct(leak["margin_pct"])} margin).</div>',
            unsafe_allow_html=True,
        )

    else:
        st.info(
            f"No lines in this selection are discounted "
            f"{leak['threshold_pct']:.0f}% or more."
        )

    bands = A.discount_bands(df)

    c1, c2 = st.columns(2)

    with c1, card("d_margin"):
        card_header(
            "Discount vs profit margin",
            "Margin earned at each discount level",
        )

        st.plotly_chart(
            charts.discount_margin_chart(bands),
            key="chart_ex_d_margin",
            **PLOT,
        )

    with c2, card("d_rev"):
        card_header(
            "Discount impact on revenue",
            "Revenue and profit by discount level",
        )

        st.plotly_chart(
            charts.discount_revenue_profit_chart(bands),
            key="chart_ex_d_rev",
            **PLOT,
        )

    st.write("")

    with card("d_leak"):
        card_header(
            "Where deep discounts hurt most",
            f"Profit on lines discounted {leak['threshold_pct']:.0f}%+, by sub-category",
        )

        lk = A.leakage_by_subcategory(df)

        if lk.empty:
            st.caption("No deeply discounted lines in this selection.")
        else:
            st.plotly_chart(
                charts.hbar(
                    lk.head(10),
                    "subcategory",
                    "profit",
                    color=charts.GREEN,
                    height=max(200, 34 * min(10, len(lk)) + 40),
                ),
                key="chart_ex_d_leak",
                **PLOT,
            )


def _regions(df) -> None:
    reg = A.region_performance(df)

    c1, c2, c3 = st.columns([1.4, 1, 1])

    with c1, card("r_rev"):
        card_header("Revenue and profit by region")

        st.plotly_chart(
            charts.region_chart(reg),
            key="chart_ex_r_rp",
            **PLOT,
        )

    with c2, card("r_margin"):
        card_header("Profit margin by region")

        st.plotly_chart(
            charts.hbar(
                reg.sort_values("margin_pct", ascending=False),
                "region",
                "margin_pct",
                kind="pct",
                color=charts.GREEN,
                height=250,
            ),
            key="chart_ex_r_m",
            **PLOT,
        )

    with c3, card("r_orders"):
        card_header("Order distribution")

        st.plotly_chart(
            charts.donut(
                list(reg["region"]),
                [int(x) for x in reg["orders"]],
            ),
            key="chart_ex_r_o",
            **PLOT,
        )

    st.write("")

    # Regional Profitability Benchmark
    with card("r_benchmark"):
        card_header(
            "Regional Profitability Benchmark",
            "Compare each region's profit margin against the overall business margin.",
        )

        benchmark = A.regional_margin_benchmark(df)

        if benchmark.empty:
            st.caption("No regional benchmarking data available.")
        else:
            overall = benchmark["overall_margin_pct"].iloc[0]

            if pd.isna(overall):
                st.info(
                    "Overall profit margin is unavailable for this selection."
                )
            else:
                st.metric(
                    "Overall business profit margin",
                    f"{overall:.2f}%",
                )

            display = benchmark.copy()

            display["margin_pct"] = display["margin_pct"].map(
                lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A"
            )

            display["overall_margin_pct"] = display[
                "overall_margin_pct"
            ].map(
                lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A"
            )

            display["margin_gap_pp"] = display["margin_gap_pp"].map(
                lambda x: f"{x:+.2f} pp" if pd.notna(x) else "N/A"
            )

            tables.show(display, height=250)

            st.caption(
                "Above Average: higher margin than the business benchmark. "
                "Below Average: lower margin. "
                "At Average: within 0.01 percentage points."
            )

    st.write("")

    with card("r_table"):
        card_header("Region summary")

        tables.show(
            metrics.group_summary(df, "region")[
                [
                    "region",
                    "revenue",
                    "profit",
                    "margin_pct",
                    "orders",
                    "aov",
                    "revenue_share_pct",
                ]
            ]
        )


def _forecast_tab(df) -> None:
    monthly = metrics.monthly_series(df)

    with card("f_main"):
        card_header(
            "Monthly revenue forecast",
            "Trend plus seasonality, tested on months the model hadn't seen",
        )

        horizon = st.slider(
            "Months to forecast",
            3,
            12,
            6,
            key="ex_horizon",
        )

        try:
            res = _forecast(monthly, horizon)
        except ValueError as exc:
            st.info(
                str(exc) + f" Widen the date range (at least {MIN_MONTHS} months)."
            )
            return

        st.plotly_chart(
            charts.forecast_chart(res),
            key="chart_ex_forecast",
            **PLOT,
        )

        m = res.metrics

        a, b, c = st.columns(3)

        with a:
            stat(
                f"Model MAE (last {m['test_months']} months)",
                fmt_money(m["mae"]),
            )

        with b:
            stat("Model RMSE", fmt_money(m["rmse"]))

        with c:
            stat(
                "Seasonal-naive MAE",
                fmt_money(m["naive_mae"])
                if m["naive_mae"] is not None
                else "n/a",
            )

        if m["naive_mae"] is not None:
            verdict = "beat" if m["beats_naive"] else "did not beat"

            st.caption(
                f"On the held-out months the model {verdict} "
                f"the simple 'same month last year' baseline. "
                f"Underlying trend: {fmt_money(res.trend_per_month)} per month."
            )

        st.caption(LIMITATIONS)


def render(df_all) -> None:
    page_header(
        "Explore",
        "Slice the business by product, customer, discount and region.",
    )

    f = filter_bar(
        df_all,
        "ex",
        categories=True,
        segments=True,
    )

    if f.df.empty:
        return empty_state()

    render_kpis(
        A.compare_kpis(f.df_scope, f.start, f.end, f.data_min),
        compact=True,
    )

    st.write("")

    tab_names = [
        "Products",
        "Customers",
        "Discounts",
        "Regions",
        "Forecast",
    ]

    tabs = st.tabs(tab_names)

    for tab, fn in zip(
        tabs,
        (
            _products,
            _customers,
            _discounts,
            _regions,
            _forecast_tab,
        ),
    ):
        with tab:
            st.write("")
            fn(f.df)

    st.write("")

    with card("table"):
        card_header(
            "Order lines",
            f"{len(f.df):,} rows match the filters. Click a column header to sort.",
        )

        shown = f.df[EXPORT_COLUMNS].sort_values(
            "order_date",
            ascending=False,
        )

        tables.show(shown, height=380)

        st.download_button(
            "Download filtered data (CSV)",
            filtered_csv(f.df),
            "nexmargin_filtered_orders.csv",
            "text/csv",
            key="ex_csv",
        )
